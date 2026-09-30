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


def _load_local_env() -> None:
    """Load simple KEY=VALUE entries from the project .env if present."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()


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


class GeminiClient:
    def __init__(self, model: str = "gemini-3.8-flash") -> None:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Google Gen AI SDK is required for Gemini runs; install google-genai first"
            ) from exc
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = model

    def complete(self, prompt: str) -> tuple[str, dict[str, Any]]:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        metadata = getattr(response, "usage_metadata", None)
        usage = {
            "input_tokens": getattr(metadata, "prompt_token_count", 0),
            "output_tokens": getattr(metadata, "candidates_token_count", 0),
        }
        return response.text or "", usage


def create_client(provider: str, model: str | None = None) -> ModelClient:
    """Create a provider client without exposing provider details to runners."""
    if provider == "anthropic":
        return AnthropicClient(model or "claude-sonnet-4-5")
    if provider == "gemini":
        return GeminiClient(model or "gemini-3.8-flash")
    raise ValueError(f"unsupported provider: {provider}")


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


def _diff_metadata(diff: str) -> dict[str, Any]:
    paths: list[str] = []
    deleted_paths: list[str] = []
    lines = diff.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("--- ") or index + 1 >= len(lines):
            continue
        old_path = line[4:].split("\t", 1)[0]
        new_line = lines[index + 1]
        if not new_line.startswith("+++ "):
            continue
        new_path = new_line[4:].split("\t", 1)[0]
        if old_path != "/dev/null":
            normalized = old_path.removeprefix("a/")
            paths.append(normalized)
            if new_path == "/dev/null":
                deleted_paths.append(normalized)
        elif new_path != "/dev/null":
            paths.append(new_path.removeprefix("b/"))
    return {
        "changed_files": sorted(set(paths)),
        "deleted_files": sorted(set(deleted_paths)),
    }


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
    changed_files: set[str] = set()
    deleted_files: set[str] = set()

    with tempfile.TemporaryDirectory(prefix=f"coding-agent-{task['id']}-") as temp_dir:
        repo_dir = Path(temp_dir) / task["repo"]
        shutil.copytree(source_root / task["repo"], repo_dir)
        for iterations in range(1, config.max_iterations + 1):
            try:
                response, model_usage = client.complete(_prompt(task, repo_dir, feedback))
                for key in usage:
                    usage[key] += int(model_usage.get(key, 0))
                diff = _extract_diff(response)
                diff_metadata = _diff_metadata(diff)
                changed_files.update(diff_metadata["changed_files"])
                deleted_files.update(diff_metadata["deleted_files"])
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
        "changed_files": sorted(changed_files),
        "deleted_files": sorted(deleted_files),
        "tests_touched": any(path.startswith("tests/") for path in changed_files),
        "tests_deleted": any(path.startswith("tests/") for path in deleted_files),
    }
    if failure:
        record["failure"] = failure[-4000:]
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    return record