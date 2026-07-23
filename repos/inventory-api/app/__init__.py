from . import db as db_module
from .wsgi import InventoryApp


def create_app(db_path=":memory:"):
    """Build a fresh (app, connection) pair backed by SQLite at db_path."""
    conn = db_module.get_connection(db_path)
    db_module.init_db(conn)
    return InventoryApp(conn), conn
