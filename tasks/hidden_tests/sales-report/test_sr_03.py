import unittest

from sales_report.report import format_currency


class TestCurrencyRounding(unittest.TestCase):
    def test_rounds_half_up_despite_float_imprecision(self):
        self.assertEqual(format_currency(2.675), "$2.68")

    def test_simple_values_still_correct(self):
        self.assertEqual(format_currency(20.0), "$20.00")
        self.assertEqual(format_currency(19.5), "$19.50")


if __name__ == "__main__":
    unittest.main()
