import os
import unittest

from sales_report.loader import load_transactions

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "data", "transactions_sample.csv")


class TestLoader(unittest.TestCase):
    def test_loads_all_rows(self):
        transactions = load_transactions(SAMPLE)
        self.assertEqual(len(transactions), 8)

    def test_fields_parsed(self):
        transactions = load_transactions(SAMPLE)
        first = transactions[0]
        self.assertEqual(first.date, "2026-01-05")
        self.assertEqual(first.category, "Tools")
        self.assertEqual(first.product, "Hammer")
        self.assertEqual(first.amount, 25.0)
        self.assertEqual(first.type, "sale")


if __name__ == "__main__":
    unittest.main()
