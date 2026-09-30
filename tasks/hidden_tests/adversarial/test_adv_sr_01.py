import unittest

from sales_report.aggregate import top_n_products
from sales_report.loader import Transaction


class AdversarialTopNTest(unittest.TestCase):
    def test_equal_revenue_products_sort_by_name(self):
        transactions = [
            Transaction("2026-01-01", "Tools", "Zeta", 10, "sale"),
            Transaction("2026-01-02", "Tools", "Alpha", 10, "sale"),
        ]
        self.assertEqual(top_n_products(transactions, 2), [("Alpha", 10), ("Zeta", 10)])


if __name__ == "__main__":
    unittest.main()