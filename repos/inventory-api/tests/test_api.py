import unittest

from app import create_app
from app import testclient as tc


class TestInventoryApi(unittest.TestCase):
    def setUp(self):
        self.app, self.conn = create_app(":memory:")

    def _create(self, name="Widget", category="Tools", price=9.99, quantity=10):
        status, payload = tc.request(
            self.app, "POST", "/items",
            json_body={"name": name, "category": category, "price": price, "quantity": quantity},
        )
        return status, payload

    def test_create_item(self):
        status, payload = self._create()
        self.assertEqual(status, 201)
        self.assertEqual(payload["name"], "Widget")
        self.assertIn("id", payload)

    def test_get_item(self):
        _, created = self._create()
        status, payload = tc.request(self.app, "GET", f"/items/{created['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(payload["id"], created["id"])

    def test_get_item_not_found(self):
        status, payload = tc.request(self.app, "GET", "/items/999")
        self.assertEqual(status, 404)

    def test_list_items_returns_all(self):
        self._create(name="A")
        self._create(name="B")
        status, payload = tc.request(self.app, "GET", "/items")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload), 2)

    def test_list_items_filter_by_category_same_case(self):
        self._create(name="A", category="Tools")
        self._create(name="B", category="Kitchen")
        status, payload = tc.request(self.app, "GET", "/items", query_string="category=Tools")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "A")

    def test_list_items_filter_by_min_price(self):
        self._create(name="Cheap", price=5.0)
        self._create(name="Pricey", price=50.0)
        status, payload = tc.request(self.app, "GET", "/items", query_string="min_price=10")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "Pricey")

    def test_update_item_full_replace(self):
        _, created = self._create(name="Old", category="Tools", price=1.0, quantity=1)
        status, payload = tc.request(
            self.app, "PUT", f"/items/{created['id']}",
            json_body={"name": "New", "category": "Kitchen", "price": 2.0, "quantity": 5},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["name"], "New")
        self.assertEqual(payload["category"], "Kitchen")
        self.assertEqual(payload["price"], 2.0)
        self.assertEqual(payload["quantity"], 5)

    def test_update_item_not_found(self):
        status, payload = tc.request(self.app, "PUT", "/items/999", json_body={"name": "X"})
        self.assertEqual(status, 404)

    def test_delete_item(self):
        _, created = self._create()
        status, payload = tc.request(self.app, "DELETE", f"/items/{created['id']}")
        self.assertEqual(status, 200)
        self.assertTrue(payload["deleted"])
        status, _ = tc.request(self.app, "GET", f"/items/{created['id']}")
        self.assertEqual(status, 404)

    def test_delete_item_not_found(self):
        status, payload = tc.request(self.app, "DELETE", "/items/999")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
