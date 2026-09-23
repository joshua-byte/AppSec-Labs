from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3
import json

HOST = "127.0.0.1"
PORT = 8001
DB_NAME = "sql_lab.db"


def initialize_database():

    conn = sqlite3.connect(DB_NAME)

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)

        conn.execute("DELETE FROM users")

        conn.executemany(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            [
                ("alice", "alice@example.com"),
                ("bob", "bob@example.com"),
                ("charlie", "charlie@example.com"),
            ],
        )

        conn.commit()

    finally:
        conn.close()


class SQLLabHandler(BaseHTTPRequestHandler):

    def send_json(self, status, data):

        body = json.dumps(
            data,
            indent=2
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):

        parsed = urlparse(self.path)

        if parsed.path != "/user":

            self.send_json(
                404,
                {"error": "Route not found"}
            )

            return

        params = parse_qs(parsed.query)

        username = params.get(
            "username",
            [""]
        )[0]

        if not username:

            self.send_json(
                400,
                {"error": "Missing username parameter"}
            )

            return

        # SECURE: parameterized query
        query = """
            SELECT id, username, email
            FROM users
            WHERE username = ?
        """

        print("\n[SQL QUERY]")
        print(query)

        print(
            "[PARAMETER]",
            repr(username)
        )

        try:

            conn = sqlite3.connect(DB_NAME)

            conn.row_factory = sqlite3.Row

            try:

                rows = conn.execute(
                    query,
                    (username,)
                ).fetchall()

                results = [
                    dict(row)
                    for row in rows
                ]

            finally:

                conn.close()

            self.send_json(
                200,
                {"users": results}
            )

        except sqlite3.Error as e:

            print(
                "[SQL ERROR]",
                e
            )

            self.send_json(
                500,
                {
                    "error":
                    "Database query failed"
                }
            )

    def log_message(self, format, *args):

        print(
            "[HTTP]",
            format % args
        )


if __name__ == "__main__":

    initialize_database()

    server = HTTPServer(
        (HOST, PORT),
        SQLLabHandler
    )

    print(
        f"SQL Injection lab running at "
        f"http://{HOST}:{PORT}"
    )

    print("Press Ctrl+C to stop.")

    server.serve_forever()