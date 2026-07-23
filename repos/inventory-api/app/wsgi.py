"""A tiny stdlib WSGI application implementing the inventory REST API.

No third-party web framework is required, so the whole eval harness can run
without a pip install step. Routes mirror what a Flask/FastAPI app would expose:

    POST   /items                 create an item
    GET    /items                 list items (?category=&min_price=&max_price=&sort_by=)
    GET    /items/{id}            fetch one item
    PUT    /items/{id}            update one item (partial body; omitted fields
                                   must be left unchanged)
    DELETE /items/{id}            delete one item
"""
import json
import re
from urllib.parse import parse_qs

from . import db

ITEM_ID_RE = re.compile(r"^/items/(\d+)$")


def _json_response(status, payload):
    body = json.dumps(payload).encode("utf-8")
    headers = [("Content-Type", "application/json"), ("Content-Length", str(len(body)))]
    return status, headers, body


class InventoryApp:
    def __init__(self, conn):
        self.conn = conn

    def __call__(self, environ, start_response):
        method = environ["REQUEST_METHOD"]
        path = environ["PATH_INFO"]
        qs = parse_qs(environ.get("QUERY_STRING", ""))

        try:
            status, headers, body = self.route(method, path, qs, environ)
        except KeyError as exc:
            status, headers, body = _json_response("400 Bad Request", {"error": f"missing field {exc}"})

        start_response(status, headers)
        return [body]

    def route(self, method, path, qs, environ):
        if path == "/items" and method == "POST":
            return self.create_item(environ)
        if path == "/items" and method == "GET":
            return self.list_items(qs)

        m = ITEM_ID_RE.match(path)
        if m:
            item_id = int(m.group(1))
            if method == "GET":
                return self.get_item(item_id)
            if method == "PUT":
                return self.update_item(item_id, environ)
            if method == "DELETE":
                return self.delete_item(item_id)

        return _json_response("404 Not Found", {"error": "not found"})

    def _read_json_body(self, environ):
        length = int(environ.get("CONTENT_LENGTH") or 0)
        raw = environ["wsgi.input"].read(length) if length else b"{}"
        return json.loads(raw or b"{}")

    def create_item(self, environ):
        data = self._read_json_body(environ)
        item = db.create_item(
            self.conn,
            name=data["name"],
            category=data["category"],
            price=data["price"],
            quantity=data["quantity"],
        )
        return _json_response("201 Created", item)

    def list_items(self, qs):
        category = qs.get("category", [None])[0]
        min_price = qs.get("min_price", [None])[0]
        max_price = qs.get("max_price", [None])[0]
        sort_by = qs.get("sort_by", [None])[0]
        items = db.list_items(
            self.conn,
            category=category,
            min_price=float(min_price) if min_price is not None else None,
            max_price=float(max_price) if max_price is not None else None,
            sort_by=sort_by,
        )
        return _json_response("200 OK", items)

    def get_item(self, item_id):
        item = db.get_item(self.conn, item_id)
        if item is None:
            return _json_response("404 Not Found", {"error": "not found"})
        return _json_response("200 OK", item)

    def update_item(self, item_id, environ):
        data = self._read_json_body(environ)
        item = db.update_item(self.conn, item_id, data)
        if item is None:
            return _json_response("404 Not Found", {"error": "not found"})
        return _json_response("200 OK", item)

    def delete_item(self, item_id):
        removed = db.delete_item(self.conn, item_id)
        if not removed:
            return _json_response("404 Not Found", {"error": "not found"})
        return _json_response("200 OK", {"deleted": True})
