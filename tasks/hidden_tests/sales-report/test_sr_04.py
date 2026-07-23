import unittest

from sales_report.aggregate import top_n_products
from sales_report.loader import Transaction


class TestTopNProducts(unittest.TestCase):
    def test_returns_top_n_by_net_revenue_descending(self):
        transactions = [
            Transaction("2026-01-01", "Tools", "Hammer", 100.0, "sale"),
            Transaction("2026-01-02", "Tools", "Wrench", 50.0, "sale"),
            Transaction("2026-01-03", "Kitchen", "Blender", 80.0, "sale"),
            Transaction("2026-01-04", "Tools", "Hammer", 30.0, "refund"),
        ]
        result = top_n_products(transactions, 2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ("Blender", 80.0))
        self.assertEqual(result[1], ("Hammer", 70.0))


if __name__ == "__main__":
    unittest.main()
