import unittest

from sales_report.aggregate import compute_totals_by_category, compute_monthly_revenue
from sales_report.loader import Transaction


class TestAggregate(unittest.TestCase):
    def test_totals_by_category_sums_sales(self):
        transactions = [
            Transaction("2026-01-05", "Tools", "Hammer", 25.0, "sale"),
            Transaction("2026-01-06", "Tools", "Wrench", 15.0, "sale"),
            Transaction("2026-01-07", "Kitchen", "Blender", 40.0, "sale"),
        ]
        totals = compute_totals_by_category(transactions)
        self.assertEqual(totals["Tools"], 40.0)
        self.assertEqual(totals["Kitchen"], 40.0)

    def test_monthly_revenue_within_one_year(self):
        transactions = [
            Transaction("2026-01-05", "Tools", "Hammer", 25.0, "sale"),
            Transaction("2026-01-06", "Tools", "Wrench", 15.0, "sale"),
            Transaction("2026-02-01", "Kitchen", "Blender", 40.0, "sale"),
        ]
        totals = compute_monthly_revenue(transactions)
        # Deliberately not asserting on the exact key format (e.g. "01" vs
        # "2026-01") -- that's precisely what task sr-02 fixes. Just check
        # the two months stay separate buckets with the right totals.
        self.assertEqual(len(totals), 2)
        self.assertEqual(sum(totals.values()), 80.0)


if __name__ == "__main__":
    unittest.main()
