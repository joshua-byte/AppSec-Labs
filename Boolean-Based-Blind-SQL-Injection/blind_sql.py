from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3
import json

HOST = "127.0.0.1"
PORT = 8003
DB_NAME = "sql_lab.db"


class BlindLabHandler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, indent=2).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path != "/check-user":
            self.send_json(404, {"error": "Route not found"})
            return

        params = parse_qs(parsed.query)
        username = params.get("username", [""])[0]

        if not username:
            self.send_json(
                400,
                {"error": "Missing username parameter"}
            )
            return

        #  parameterized SQL query.
        query = """
            SELECT id
            FROM users
            WHERE username = ?
        """

        try:
            with sqlite3.connect(DB_NAME) as conn:
                row = conn.execute(
                    query,
                    (username,)
                ).fetchone()

            self.send_json(
                200,
                {"exists": row is not None}
            )

        except sqlite3.Error:
            #details out of client responses.
            self.send_json(
                500,
                {"error": "Internal server error"}
            )

    def log_message(self, format, *args):
        print("[HTTP]", format % args)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), BlindLabHandler)

    print(
        f"Secure Blind SQLi lab running at "
        f"http://{HOST}:{PORT}"
    )
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nServer stopped.")

    finally:
        server.server_close()