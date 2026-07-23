"""A minimal WSGI test client (stdlib only) -- same idea as Flask's test_client,
built by hand so tests don't need any third-party HTTP library.
"""
import io
import json


def request(app, method, path, json_body=None, query_string=""):
    body_bytes = b""
    if json_body is not None:
        body_bytes = json.dumps(json_body).encode("utf-8")

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query_string,
        "CONTENT_LENGTH": str(len(body_bytes)),
        "wsgi.input": io.BytesIO(body_bytes),
        "wsgi.errors": io.StringIO(),
    }

    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    result = app(environ, start_response)
    raw = b"".join(result)
    status_code = int(captured["status"].split(" ", 1)[0])
    payload = json.loads(raw) if raw else None
    return status_code, payload
