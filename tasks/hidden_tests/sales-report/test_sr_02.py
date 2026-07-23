import unittest

from sales_report.aggregate import compute_monthly_revenue
from sales_report.loader import Transaction


class TestMonthlyRevenueByYear(unittest.TestCase):
    def test_same_month_different_years_kept_separate(self):
        transactions = [
            Transaction("2026-01-05", "Tools", "Hammer", 25.0, "sale"),
            Transaction("2027-01-05", "Tools", "Hammer", 40.0, "sale"),
        ]
        totals = compute_monthly_revenue(transactions)
        self.assertEqual(totals.get("2026-01"), 25.0)
        self.assertEqual(totals.get("2027-01"), 40.0)
        self.assertNotIn("01", totals)


if __name__ == "__main__":
    unittest.main()
