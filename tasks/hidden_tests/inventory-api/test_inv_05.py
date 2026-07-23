import unittest

from app import create_app
from app import testclient as tc


class TestRestock(unittest.TestCase):
    def setUp(self):
        self.app, self.conn = create_app(":memory:")

    def test_restock_increments_quantity(self):
        _, created = tc.request(
            self.app, "POST", "/items",
            json_body={"name": "Widget", "category": "Tools", "price": 9.99, "quantity": 10},
        )
        status, payload = tc.request(
            self.app, "POST", f"/items/{created['id']}/restock",
            json_body={"amount": 5},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["quantity"], 15)

        status, fetched = tc.request(self.app, "GET", f"/items/{created['id']}")
        self.assertEqual(fetched["quantity"], 15)


if __name__ == "__main__":
    unittest.main()
