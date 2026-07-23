import unittest

from app import create_app
from app import testclient as tc


class TestSortBy(unittest.TestCase):
    def setUp(self):
        self.app, self.conn = create_app(":memory:")

    def _create(self, name, price):
        tc.request(
            self.app, "POST", "/items",
            json_body={"name": name, "category": "Tools", "price": price, "quantity": 1},
        )

    def test_sort_by_price_ascending(self):
        self._create("C", 30.0)
        self._create("A", 10.0)
        self._create("B", 20.0)

        status, payload = tc.request(self.app, "GET", "/items", query_string="sort_by=price")
        self.assertEqual(status, 200)
        self.assertEqual([item["name"] for item in payload], ["A", "B", "C"])

    def test_sort_by_name_ascending(self):
        self._create("Charlie", 1.0)
        self._create("Alpha", 1.0)
        self._create("Bravo", 1.0)

        status, payload = tc.request(self.app, "GET", "/items", query_string="sort_by=name")
        self.assertEqual([item["name"] for item in payload], ["Alpha", "Bravo", "Charlie"])


if __name__ == "__main__":
    unittest.main()
