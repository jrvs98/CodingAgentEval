import unittest

from app import create_app
from app import testclient as tc


class TestPartialUpdatePreservesFields(unittest.TestCase):
    def setUp(self):
        self.app, self.conn = create_app(":memory:")

    def test_partial_update_only_changes_given_field(self):
        _, created = tc.request(
            self.app, "POST", "/items",
            json_body={"name": "Widget", "category": "Tools", "price": 9.99, "quantity": 10},
        )
        status, updated = tc.request(
            self.app, "PUT", f"/items/{created['id']}",
            json_body={"quantity": 5},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["quantity"], 5)
        self.assertEqual(updated["name"], "Widget")
        self.assertEqual(updated["category"], "Tools")
        self.assertEqual(updated["price"], 9.99)


if __name__ == "__main__":
    unittest.main()
