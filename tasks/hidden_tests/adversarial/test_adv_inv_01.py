import unittest

from app import db
from app.testclient import request
from app.wsgi import InventoryApp


class AdversarialSortValidationTest(unittest.TestCase):
    def test_unknown_sort_field_is_rejected(self):
        conn = db.get_connection()
        db.init_db(conn)
        db.create_item(conn, "Widget", "Tools", 10, 2)
        status, payload = request(InventoryApp(conn), "GET", "/items", query_string="sort_by=quantity")
        self.assertEqual(status, 400)
        self.assertIn("sort_by", payload["error"])


if __name__ == "__main__":
    unittest.main()