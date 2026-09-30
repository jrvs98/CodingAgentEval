import json
import difflib
import tempfile
import unittest
from pathlib import Path

from eval.agent import AgentConfig, create_client, run_task


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