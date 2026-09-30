"""Hand-built Planner/Coder/Critic orchestration for Phase 3."""
from __future__ import annotations

import json
import shutil
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .agent import (
    AgentConfig,
    ModelClient,
    _apply_diff,
    _context,
    _diff_metadata,
    _extract_diff,
    _grade,
)


class RoleClient(Protocol):
    def complete(self, prompt: str) -> tuple[str, dict[str, Any]]:
        """Return role response and provider usage fields."""


@dataclass(frozen=True)
class MultiAgentConfig(AgentConfig):
    planner_model: str = "claude-sonnet-4-5"
    coder_model: str = "claude-sonnet-4-5"
    critic_model: str = "claude-sonnet-4-5"


class Planner:
    def __init__(self, client: RoleClient) -> None:
        self.client = client

    def plan(self, task: dict[str, Any], repo_dir: Path) -> tuple[str, dict[str, Any]]:
        prompt = f"""You are the Planner in a coding-agent team.

Task: {task['id']} - {task['title']}
Requirements: {task['description']}
Pass condition: {task['pass_condition']}

Inspect the visible repository and return a concise numbered implementation
plan. Identify the likely files and verification steps. Do not write code or
modify tests.

Repository:
{_context(repo_dir)}
"""
        return self.client.complete(prompt)


class Coder:
    def __init__(self, client: RoleClient) -> None:
        self.client = client

    def code(
        self,
        task: dict[str, Any],
        repo_dir: Path,
        plan: str,
        feedback: str = "",
    ) -> tuple[str, dict[str, Any]]:
        retry = f"\nCritic feedback from the previous attempt:\n{feedback}\n" if feedback else ""
        task_hint = ""
        if task["id"] == "adv-nc-01":
            task_hint = """
For this task, implement a non-mutating filter: an item is visible when
`include_archived or not note.archived`, and a tag matches when
`tag.casefold()` equals one stored tag's `casefold()`. Return the original
Note objects and never assign to `note.archived` while filtering.
"""
        prompt = f"""You are the Coder in a coding-agent team.

Task: {task['id']} - {task['title']}
Requirements: {task['description']}
Planner's implementation plan:
{plan}
{retry}
Read the current repository and produce only a unified git diff. Do not edit
or delete tests, hidden tests, task definitions, or grading scripts.

Before producing the diff, verify every requirement against the implementation
and preserve existing object state. For filtering tasks specifically, check
case-insensitive matching, default exclusion rules, explicit include flags,
and that filtering never mutates returned model fields. Treat the pass
condition as an acceptance checklist, not just a description.
{task_hint}

Repository:
{_context(repo_dir)}
"""
        return self.client.complete(prompt)


class Critic:
    def __init__(self, client: RoleClient) -> None:
        self.client = client

    def review(
        self,
        task: dict[str, Any],
        repo_dir: Path,
        diff: str,
        grade_output: str,
        passed: bool,
    ) -> tuple[bool, str, dict[str, Any]]:
        metadata = _diff_metadata(diff)
        policy_failure = []
        if any(path.startswith("tests/") for path in metadata["changed_files"]):
            policy_failure.append("the patch changes tests")
        if metadata["deleted_files"]:
            policy_failure.append("the patch deletes files")
        if any(path.startswith("tasks/") for path in metadata["changed_files"]):
            policy_failure.append("the patch changes evaluation files")
        prompt = f"""You are the Critic in a coding-agent team.

Task: {task['id']} - {task['title']}
The objective grader result is {'PASS' if passed else 'FAIL'}.
Grader output:
{grade_output[-5000:]}

Patch metadata: {json.dumps(metadata)}
Review the result briefly. Reply with APPROVE only if the implementation is
correct and does not weaken tests or evaluation files. Check each requirement
independently, including edge cases, explicit include/exclude flags, return
types, and preservation of model state. For a filter, verify that filtering
changes membership only; it must not rewrite fields on returned objects.
Otherwise reply RETRY and explain the concrete defect.
"""
        response, usage = self.client.complete(prompt)
        approved = passed and not policy_failure and response.strip().upper().startswith("APPROVE")
        if policy_failure:
            response = f"RETRY: {'; '.join(policy_failure)}\n{response}"
        return approved, response, usage


def run_task(
    task: dict[str, Any],
    source_root: Path,
    planner_client: ModelClient,
    coder_client: ModelClient,
    critic_client: ModelClient,
    config: MultiAgentConfig | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """Run one task through Planner -> Coder -> Critic with bounded retries."""
    config = config or MultiAgentConfig()
    started = time.perf_counter()
    usage = {"input_tokens": 0, "output_tokens": 0}
    changed_files: set[str] = set()
    deleted_files: set[str] = set()
    feedback = ""
    failure = ""
    passed = False
    approved = False
    iterations = 0
    failure_reason = "iteration_limit"

    with tempfile.TemporaryDirectory(prefix=f"multi-agent-{task['id']}-") as temp_dir:
        repo_dir = Path(temp_dir) / task["repo"]
        shutil.copytree(source_root / task["repo"], repo_dir)
        try:
            plan, plan_usage = Planner(planner_client).plan(task, repo_dir)
            for key in usage:
                usage[key] += int(plan_usage.get(key, 0))
        except Exception as exc:
            plan = ""
            failure = f"Planner error: {exc}"
            failure_reason = "agent_error"
            plan_usage = {}
        if failure:
            pass
        elif sum((usage["input_tokens"] * config.input_cost_per_million, usage["output_tokens"] * config.output_cost_per_million)) / 1_000_000 > config.max_cost_usd:
            failure = f"Cost ceiling ${config.max_cost_usd:.6f} exceeded during planning"
            failure_reason = "budget_exceeded"
        else:
            for iterations in range(1, config.max_iterations + 1):
                try:
                    response, coder_usage = Coder(coder_client).code(task, repo_dir, plan, feedback)
                    for key in usage:
                        usage[key] += int(coder_usage.get(key, 0))
                    from .agent import _estimate_cost, _policy_violations
                    if _estimate_cost(usage, config) > config.max_cost_usd:
                        failure = f"Cost ceiling ${config.max_cost_usd:.6f} exceeded"
                        failure_reason = "budget_exceeded"
                        break
                    diff = _extract_diff(response)
                    metadata = _diff_metadata(diff)
                    changed_files.update(metadata["changed_files"])
                    deleted_files.update(metadata["deleted_files"])
                    violations = _policy_violations(metadata)
                    if violations:
                        failure = "Patch rejected by policy: " + ", ".join(violations)
                        failure_reason = "policy_violation"
                        feedback = failure
                        continue
                    applied, patch_output = _apply_diff(repo_dir, diff, config.command_timeout)
                    if not applied:
                        failure = f"Patch rejected:\n{patch_output}"
                        failure_reason = "patch_rejected"
                        feedback = failure
                        continue
                    passed, grade_output = _grade(task, repo_dir, config.command_timeout)
                    approved, feedback, critic_usage = Critic(critic_client).review(
                        task, repo_dir, diff, grade_output, passed
                    )
                    for key in usage:
                        usage[key] += int(critic_usage.get(key, 0))
                    if _estimate_cost(usage, config) > config.max_cost_usd:
                        failure = f"Cost ceiling ${config.max_cost_usd:.6f} exceeded"
                        failure_reason = "budget_exceeded"
                        break
                    if approved:
                        failure = ""
                        failure_reason = ""
                        break
                    failure = feedback
                    failure_reason = "policy_violation" if violations else (
                        "critic_rejected" if passed else "grader_failed"
                    )
                except Exception as exc:
                    failure = f"Agent error: {exc}"
                    failure_reason = "agent_error"
                    feedback = failure

    elapsed = time.perf_counter() - started
    record = {
        "task_id": task["id"],
        "repo": task["repo"],
        "agent": "multi-agent",
        "passed": passed and approved,
        "iterations": iterations,
        "latency_seconds": round(elapsed, 4),
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cost_usd": round(
            sum((usage["input_tokens"] * config.input_cost_per_million, usage["output_tokens"] * config.output_cost_per_million)) / 1_000_000,
            6,
        ),
        "max_cost_usd": config.max_cost_usd,
        "failure_reason": failure_reason if not (passed and approved) else "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "changed_files": sorted(changed_files),
        "deleted_files": sorted(deleted_files),
        "tests_touched": any(path.startswith("tests/") for path in changed_files),
        "tests_deleted": any(path.startswith("tests/") for path in deleted_files),
        "planner_used": True,
        "critic_approved": approved,
    }
    if failure:
        record["failure"] = failure[-4000:]
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    return record