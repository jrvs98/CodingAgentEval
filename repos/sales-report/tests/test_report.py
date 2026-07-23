import unittest

from sales_report.report import generate_report, format_currency
from sales_report.loader import Transaction


class TestReport(unittest.TestCase):
    def test_generate_report_contains_sections(self):
        transactions = [
            Transaction("2026-01-05", "Tools", "Hammer", 25.0, "sale"),
        ]
        text = generate_report(transactions)
        self.assertIn("Revenue by Category", text)
        self.assertIn("Revenue by Month", text)
        self.assertIn("Tools", text)

    def test_format_currency_simple_values(self):
        self.assertEqual(format_currency(20.0), "$20.00")
        self.assertEqual(format_currency(19.5), "$19.50")


if __name__ == "__main__":
    unittest.main()
