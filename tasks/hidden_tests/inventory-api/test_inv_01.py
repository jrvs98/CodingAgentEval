import unittest

from app import create_app
from app import testclient as tc


class TestCategoryFilterCaseInsensitive(unittest.TestCase):
    def setUp(self):
        self.app, self.conn = create_app(":memory:")

    def _create(self, name, category, price=9.99, quantity=10):
        return tc.request(
            self.app, "POST", "/items",
            json_body={"name": name, "category": category, "price": price, "quantity": quantity},
        )

    def test_filter_matches_regardless_of_case(self):
        self._create("Hammer", "Tools")
        self._create("Blender", "Kitchen")

        status, payload = tc.request(self.app, "GET", "/items", query_string="category=tools")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "Hammer")

        status, payload = tc.request(self.app, "GET", "/items", query_string="category=TOOLS")
        self.assertEqual(len(payload), 1)


if __name__ == "__main__":
    unittest.main()
