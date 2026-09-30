import unittest

from app import db
from app.testclient import request
from app.wsgi import InventoryApp


class AdversarialRestockValidationTest(unittest.TestCase):
    def test_non_positive_restock_does_not_change_quantity(self):
        conn = db.get_connection()
        db.init_db(conn)
        item = db.create_item(conn, "Widget", "Tools", 10, 2)
        app = InventoryApp(conn)
        for amount in (0, -1, True, 1.5):
            status, payload = request(app, "POST", f"/items/{item['id']}/restock", {"amount": amount})
            self.assertEqual(status, 400)
            self.assertIn("amount", payload["error"])
        self.assertEqual(db.get_item(conn, item["id"])["quantity"], 2)


if __name__ == "__main__":
    unittest.main()