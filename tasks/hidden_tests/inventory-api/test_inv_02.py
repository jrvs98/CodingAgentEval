import unittest

from app import create_app
from app import testclient as tc


class TestMaxPriceInclusive(unittest.TestCase):
    def setUp(self):
        self.app, self.conn = create_app(":memory:")

    def _create(self, name, price):
        return tc.request(
            self.app, "POST", "/items",
            json_body={"name": name, "category": "Tools", "price": price, "quantity": 1},
        )

    def test_item_at_exact_max_price_is_included(self):
        self._create("Exactly Fifty", 50.0)
        self._create("Over Fifty", 51.0)

        status, payload = tc.request(self.app, "GET", "/items", query_string="max_price=50")
        self.assertEqual(status, 200)
        names = [item["name"] for item in payload]
        self.assertIn("Exactly Fifty", names)
        self.assertNotIn("Over Fifty", names)


if __name__ == "__main__":
    unittest.main()
