import difflib
import json
import tempfile
import unittest
from pathlib import Path

from eval.multi_agent import Critic, MultiAgentConfig, run_task

ROOT = Path(__file__).resolve().parents[1]


class FakeRoleClient:
    def __init__(self, role):
        self.role = role

    def complete(self, prompt):
        if self.role == "planner":
            return "1. Inspect the existing implementation.\n2. Preserve tests and verify the task.", {"input_tokens": 10, "output_tokens": 20}
        if self.role == "critic":
            return "APPROVE: grader and patch policy checks pass.", {"input_tokens": 15, "output_tokens": 10}
        path = ROOT / "repos" / "notes-cli" / "notes_cli" / "storage.py"
        original = path.read_text()
        current_return = next(
            line for line in original.splitlines() if line.startswith("    return [n for n in notes")
        )
        updated = original.replace(current_return, current_return + "  # reviewed by coder", 1)
        diff = "".join(difflib.unified_diff(
            original.splitlines(True), updated.splitlines(True),
            fromfile="a/notes_cli/storage.py", tofile="b/notes_cli/storage.py",
        ))
        return f"```diff\n{diff}```", {"input_tokens": 30, "output_tokens": 40}


class MultiAgentTests(unittest.TestCase):
    def test_planner_error_is_recorded_instead_of_escaping(self):
        class FailingClient:
            def complete(self, prompt):
                raise RuntimeError("provider unavailable")

        tasks = json.loads((ROOT / "tasks" / "tasks.json").read_text())
        task = next(task for task in tasks if task["id"] == "nc-01")
        with tempfile.TemporaryDirectory() as temp_dir:
            record = run_task(
                task,
                ROOT / "repos",
                FailingClient(),
                FailingClient(),
                FailingClient(),
                MultiAgentConfig(max_iterations=1),
                Path(temp_dir) / "runs.jsonl",
            )
        self.assertFalse(record["passed"])
        self.assertEqual(record["failure_reason"], "agent_error")
        self.assertIn("provider unavailable", record["failure"])

    def test_critic_rejects_patch_that_deletes_a_test(self):
        deleted_test = "--- a/tests/test_app.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-test\n"
        approved, feedback, _ = Critic(FakeRoleClient("critic")).review(
            {"id": "x", "title": "task"},
            ROOT,
            deleted_test,
            "baseline=PASS\nhidden=PASS",
            True,
        )
        self.assertFalse(approved)
        self.assertIn("deletes files", feedback)

    def test_orchestrator_runs_all_roles_and_logs_role_metrics(self):
        tasks = json.loads((ROOT / "tasks" / "tasks.json").read_text())
        task = next(task for task in tasks if task["id"] == "nc-01")
        with tempfile.TemporaryDirectory() as temp_dir:
            record = run_task(
                task,
                ROOT / "repos",
                FakeRoleClient("planner"),
                FakeRoleClient("coder"),
                FakeRoleClient("critic"),
                MultiAgentConfig(max_iterations=1),
                Path(temp_dir) / "runs.jsonl",
            )
        self.assertTrue(record["passed"])
        self.assertTrue(record["planner_used"])
        self.assertTrue(record["critic_approved"])
        self.assertEqual(record["input_tokens"], 55)
        self.assertEqual(record["output_tokens"], 70)


if __name__ == "__main__":
    unittest.main()