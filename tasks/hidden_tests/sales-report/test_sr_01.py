import unittest

from sales_report.aggregate import compute_totals_by_category
from sales_report.loader import Transaction


class TestRefundsSubtract(unittest.TestCase):
    def test_refund_reduces_category_total(self):
        transactions = [
            Transaction("2026-01-05", "Tools", "Hammer", 25.0, "sale"),
            Transaction("2026-01-06", "Tools", "Hammer", 25.0, "refund"),
        ]
        totals = compute_totals_by_category(transactions)
        self.assertEqual(totals["Tools"], 0.0)

    def test_mixed_sales_and_refunds(self):
        transactions = [
            Transaction("2026-01-05", "Tools", "Hammer", 25.0, "sale"),
            Transaction("2026-01-06", "Tools", "Wrench", 15.0, "sale"),
            Transaction("2026-01-07", "Tools", "Hammer", 25.0, "refund"),
        ]
        totals = compute_totals_by_category(transactions)
        self.assertEqual(totals["Tools"], 15.0)


if __name__ == "__main__":
    unittest.main()
