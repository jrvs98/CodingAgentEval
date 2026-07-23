import unittest

from sales_report.aggregate import pivot_category_month
from sales_report.report import generate_report
from sales_report.loader import Transaction


class TestCategoryMonthPivot(unittest.TestCase):
    def test_pivot_structure(self):
        transactions = [
            Transaction("2026-01-01", "Tools", "Hammer", 25.0, "sale"),
            Transaction("2026-02-01", "Tools", "Wrench", 15.0, "sale"),
            Transaction("2026-01-05", "Kitchen", "Blender", 40.0, "sale"),
        ]
        pivot = pivot_category_month(transactions)
        self.assertEqual(pivot["Tools"]["2026-01"], 25.0)
        self.assertEqual(pivot["Tools"]["2026-02"], 15.0)
        self.assertEqual(pivot["Kitchen"]["2026-01"], 40.0)

    def test_report_includes_pivot_section(self):
        transactions = [
            Transaction("2026-01-01", "Tools", "Hammer", 25.0, "sale"),
        ]
        text = generate_report(transactions)
        self.assertIn("Category by Month", text)


if __name__ == "__main__":
    unittest.main()
