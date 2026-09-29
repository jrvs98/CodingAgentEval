"""Single-agent coding baseline used by the evaluation harness."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


class ModelClient(Protocol):
    def complete(self, prompt: str) -> tuple[str, dict[str, Any]]:
        """Return model text and provider usage fields."""


class AnthropicClient:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Anthropic SDK is required for live runs; install anthropic first"
            ) from exc
        self.client = Anthropic()
        self.model = model

    def complete(self, prompt: str) -> tuple[str, dict[str, Any]]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "\n".join(block.text for block in response.content if hasattr(block, "text"))
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
        }
        return text, usage


@dataclass(frozen=True)
class AgentConfig:
    max_iterations: int = 3
    command_timeout: int = 60
    input_cost_per_million: float = 3.0
    output_cost_per_million: float = 15.0


def _run(command: list[str], cwd: Path, timeout: int) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env={**os.environ, "PYTHONPATH": str(cwd)},
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        return False, f"Timed out after {timeout}s\n{output}"
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def _grade(task: dict[str, Any], repo_dir: Path, timeout: int) -> tuple[bool, str]:
    baseline_ok, baseline_output = _run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        repo_dir,
        timeout,
    )
    hidden_path = Path(__file__).resolve().parents[1] / task["hidden_test"]
    hidden_ok, hidden_output = _run([sys.executable, str(hidden_path)], repo_dir, timeout)
    report = (
        f"baseline={'PASS' if baseline_ok else 'FAIL'}\n{baseline_output[-4000:]}\n"
        f"hidden={'PASS' if hidden_ok else 'FAIL'}\n{hidden_output[-4000:]}"
    )
    return baseline_ok and hidden_ok, report


def _context(repo_dir: Path) -> str:
    files: list[str] = []
    for path in sorted(repo_dir.rglob("*.py")):
        if any(part in {".git", "__pycache__"} for part in path.parts):
            continue
        relative = path.relative_to(repo_dir)
        files.append(f"\n--- {relative} ---\n{path.read_text()}")
    return "".join(files)


def _extract_diff(response: str) -> str:
    match = re.search(r"```(?:diff|patch)?\s*\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip() + "\n"
    if response.lstrip().startswith(("diff --git", "--- ")):
        return response.strip() + "\n"
    raise ValueError("model response did not contain a unified diff")


def _apply_diff(repo_dir: Path, diff: str, timeout: int) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "apply", "--whitespace=nowarn"],
            cwd=repo_dir,
            input=diff,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"Timed out applying patch after {timeout}s"
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def _prompt(task: dict[str, Any], repo_dir: Path, feedback: str = "") -> str:
    retry = f"\nPrevious attempt feedback:\n{feedback}\n" if feedback else ""
    return f"""You are a coding agent working on a small Python repository.

Task: {task['id']} - {task['title']}
Requirements: {task['description']}
Pass condition: {task['pass_condition']}

Read the repository below and produce only a unified git diff. Do not edit or
delete tests. Do not mention hidden tests or invent files outside the repo.
{retry}
Repository files:
{_context(repo_dir)}
"""


def run_task(
    task: dict[str, Any],
    source_root: Path,
    client: ModelClient,
    config: AgentConfig | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    config = config or AgentConfig()
    started = time.perf_counter()
    usage = {"input_tokens": 0, "output_tokens": 0}
    feedback = ""
    passed = False
    failure = ""
    iterations = 0

    with tempfile.TemporaryDirectory(prefix=f"coding-agent-{task['id']}-") as temp_dir:
        repo_dir = Path(temp_dir) / task["repo"]
        shutil.copytree(source_root / task["repo"], repo_dir)
        for iterations in range(1, config.max_iterations + 1):
            try:
                response, model_usage = client.complete(_prompt(task, repo_dir, feedback))
                for key in usage:
                    usage[key] += int(model_usage.get(key, 0))
                diff = _extract_diff(response)
                applied, patch_output = _apply_diff(repo_dir, diff, config.command_timeout)
                if not applied:
                    failure = f"Patch rejected:\n{patch_output}"
                    feedback = failure
                    continue
            except Exception as exc:
                failure = f"Agent error: {exc}"
                feedback = failure
                continue

            passed, feedback = _grade(task, repo_dir, config.command_timeout)
            if passed:
                failure = ""
                break
            failure = feedback

    elapsed = time.perf_counter() - started
    record = {
        "task_id": task["id"],
        "repo": task["repo"],
        "agent": "single-agent-baseline",
        "passed": passed,
        "iterations": iterations,
        "latency_seconds": round(elapsed, 4),
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cost_usd": round(
            usage["input_tokens"] * config.input_cost_per_million / 1_000_000
            + usage["output_tokens"] * config.output_cost_per_million / 1_000_000,
            6,
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if failure:
        record["failure"] = failure[-4000:]
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    return record