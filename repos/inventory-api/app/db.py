"""SQLite-backed persistence for inventory items."""
from __future__ import annotations

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
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    if sort_by in ("price", "name"):
        query += f" ORDER BY {sort_by} ASC"
    rows = conn.execute(query, params).fetchall()
    items = [dict(r) for r in rows]
    return items


def update_item(conn, item_id, fields: dict) -> dict | None:
    """Update only the fields provided in `fields`; leave the rest unchanged."""
    current = get_item(conn, item_id)
    if current is None:
        return None
    name = fields["name"] if "name" in fields else current["name"]
    category = fields["category"] if "category" in fields else current["category"]
    price = fields["price"] if "price" in fields else current["price"]
    quantity = fields["quantity"] if "quantity" in fields else current["quantity"]
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


def restock_item(conn, item_id, amount) -> dict | None:
    """Increase an item's quantity and return the updated item."""
    cur = conn.execute(
        "UPDATE items SET quantity = quantity + ? WHERE id = ?",
        (amount, item_id),
    )
    conn.commit()
    return get_item(conn, item_id) if cur.rowcount else None


def low_stock_items(conn, threshold) -> list:
    """Return items whose quantity is at or below ``threshold``."""
    rows = conn.execute(
        "SELECT * FROM items WHERE quantity <= ?",
        (threshold,),
    ).fetchall()
    return [dict(row) for row in rows]
