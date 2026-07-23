"""SQLite-backed persistence for inventory items."""
import sqlite3


def get_connection(db_path=":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def create_item(conn, name, category, price, quantity) -> dict:
    cur = conn.execute(
        "INSERT INTO items (name, category, price, quantity) VALUES (?, ?, ?, ?)",
        (name, category, price, quantity),
    )
    conn.commit()
    return get_item(conn, cur.lastrowid)


def get_item(conn, item_id) -> dict | None:
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def list_items(conn, category=None, min_price=None, max_price=None, sort_by=None) -> list:
    """List items, optionally filtered by category (case-insensitive) and price range.

    `sort_by` may be "price" or "name" (ascending).
    """
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    if category is not None:
        query += " AND category = ?"
        params.append(category)
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price < ?"
        params.append(max_price)
    rows = conn.execute(query, params).fetchall()
    items = [dict(r) for r in rows]
    return items


def update_item(conn, item_id, fields: dict) -> dict | None:
    """Update only the fields provided in `fields`; leave the rest unchanged."""
    current = get_item(conn, item_id)
    if current is None:
        return None
    name = fields.get("name")
    category = fields.get("category")
    price = fields.get("price")
    quantity = fields.get("quantity")
    conn.execute(
        "UPDATE items SET name=?, category=?, price=?, quantity=? WHERE id=?",
        (name, category, price, quantity, item_id),
    )
    conn.commit()
    return get_item(conn, item_id)


def delete_item(conn, item_id) -> bool:
    cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    return cur.rowcount > 0
