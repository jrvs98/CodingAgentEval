import unittest

from app import create_app
from app import testclient as tc


class TestLowStock(unittest.TestCase):
    def setUp(self):
        self.app, self.conn = create_app(":memory:")

    def _create(self, name, quantity):
        tc.request(
            self.app, "POST", "/items",
            json_body={"name": name, "category": "Tools", "price": 1.0, "quantity": quantity},
        )

    def test_low_stock_returns_items_at_or_below_threshold(self):
        self._create("Plenty", 100)
        self._create("Exactly At Threshold", 5)
        self._create("Below Threshold", 2)

        status, payload = tc.request(self.app, "GET", "/items/low-stock", query_string="threshold=5")
        self.assertEqual(status, 200)
        names = sorted(item["name"] for item in payload)
        self.assertEqual(names, ["Below Threshold", "Exactly At Threshold"])

    def test_item_id_route_still_works(self):
        # regression guard: the new /items/low-stock route must not break /items/{id}
        _, created = tc.request(
            self.app, "POST", "/items",
            json_body={"name": "Widget", "category": "Tools", "price": 1.0, "quantity": 1},
        )
        status, payload = tc.request(self.app, "GET", f"/items/{created['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(payload["name"], "Widget")


if __name__ == "__main__":
    unittest.main()
