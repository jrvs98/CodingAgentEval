import unittest

from eval.agent import _diff_metadata
from eval.report import build_report


class ReportTests(unittest.TestCase):
    def test_diff_metadata_detects_deleted_files(self):
        metadata = _diff_metadata(
            "--- a/tests/test_app.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-test\n"
        )
        self.assertEqual(metadata["changed_files"], ["tests/test_app.py"])
        self.assertEqual(metadata["deleted_files"], ["tests/test_app.py"])

    def test_report_aggregates_metrics_and_flags_qualitative_violations(self):
        records = [
            {
                "task_id": "a",
                "passed": True,
                "cost_usd": 1,
                "latency_seconds": 2,
                "iterations": 1,
                "changed_files": ["app.py"],
                "tests_touched": False,
                "tests_deleted": False,
            },
            {
                "task_id": "b",
                "passed": False,
                "cost_usd": 3,
                "latency_seconds": 6,
                "iterations": 3,
                "changed_files": ["tests/test_app.py", "tasks/tasks.json"],
                "tests_touched": True,
                "tests_deleted": True,
            },
        ]
        report = build_report(records)
        self.assertEqual(report["runs"], 2)
        self.assertEqual(report["pass_rate"], 0.5)
        self.assertEqual(report["median_cost_usd"], 2.0)
        self.assertEqual(report["cost_per_success_usd"], 4.0)
        self.assertEqual(report["qualitative_violations"], [{
            "task_id": "b",
            "violations": ["tests_touched", "tests_deleted", "grader_or_task_files_touched"],
        }])


if __name__ == "__main__":
    unittest.main()