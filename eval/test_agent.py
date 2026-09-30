import json
import difflib
import tempfile
import unittest
from pathlib import Path

from eval.agent import AgentConfig, _apply_diff, create_client, run_task


ROOT = Path(__file__).resolve().parents[1]


class FakeClient:
    def complete(self, prompt):
        path = ROOT / "repos" / "notes-cli" / "notes_cli" / "storage.py"
        original = path.read_text()
        buggy_return = "    return [n for n in notes if query in n.title or query in n.body]"
        if buggy_return in original:
            updated = original.replace(
                buggy_return,
                "    needle = query.casefold()\n"
                "    return [n for n in notes if needle in n.title.casefold() or needle in n.body.casefold()]",
            )
        else:
            current_return = next(
                line for line in original.splitlines() if line.startswith("    return [n for n in notes")
            )
            updated = original.replace(current_return, current_return + "  # preserve search behavior")
        diff = "".join(
            difflib.unified_diff(
                original.splitlines(True),
                updated.splitlines(True),
                fromfile="a/notes_cli/storage.py",
                tofile="b/notes_cli/storage.py",
            )
        )
        return (
            f"```diff\n{diff}```",
            {"input_tokens": 100, "output_tokens": 50},
        )


class AgentRunnerTests(unittest.TestCase):
    def test_plain_repository_paths_are_accepted_in_diffs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "app").mkdir()
            (repo / "app" / "value.py").write_text("VALUE = 1\n")
            applied, output = _apply_diff(
                repo,
                "--- app/value.py\n+++ app/value.py\n@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n",
                10,
            )
            self.assertTrue(applied, output)
            self.assertEqual((repo / "app" / "value.py").read_text(), "VALUE = 2\n")

    def test_cost_ceiling_stops_before_patch_application(self):
        class ExpensiveClient:
            calls = 0

            def complete(self, prompt):
                self.calls += 1
                return "not applied", {"input_tokens": 1_000_000, "output_tokens": 0}

        client = ExpensiveClient()
        tasks = json.loads((ROOT / "tasks" / "tasks.json").read_text())
        task = next(task for task in tasks if task["id"] == "nc-01")
        with tempfile.TemporaryDirectory() as temp_dir:
            record = run_task(
                task,
                ROOT / "repos",
                client,
                AgentConfig(max_iterations=3, max_cost_usd=0.01),
                Path(temp_dir) / "runs.jsonl",
            )
        self.assertEqual(client.calls, 1)
        self.assertFalse(record["passed"])
        self.assertEqual(record["failure_reason"], "budget_exceeded")

    def test_client_factory_rejects_unknown_provider(self):
        with self.assertRaisesRegex(ValueError, "unsupported provider"):
            create_client("unknown")

    def test_fake_client_solves_task_in_isolated_copy_and_logs_metrics(self):
        tasks = json.loads((ROOT / "tasks" / "tasks.json").read_text())
        task = next(task for task in tasks if task["id"] == "nc-01")
        source_path = ROOT / "repos" / "notes-cli" / "notes_cli" / "storage.py"
        source_before = source_path.read_text()
        with tempfile.TemporaryDirectory() as temp_dir:
            record = run_task(
                task,
                ROOT / "repos",
                FakeClient(),
                AgentConfig(max_iterations=1),
                Path(temp_dir) / "runs.jsonl",
            )
            self.assertTrue(record["passed"])
            self.assertEqual(record["iterations"], 1)
            self.assertEqual(record["input_tokens"], 100)
            self.assertEqual(record["output_tokens"], 50)
            self.assertEqual(source_path.read_text(), source_before)


if __name__ == "__main__":
    unittest.main()