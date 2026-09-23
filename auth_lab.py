from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3
import json
import hashlib
import secrets
import hmac
import time
from http.cookies import SimpleCookie

HOST = "127.0.0.1"
PORT = 8004
DB_NAME = "auth_lab.db"

# In-memory sessions: token -> user ID and expiry
SESSIONS = {}
SESSION_TTL = 1800

# Demo credentials (local training only)
USERS = {
    "alice": "alice123",
    "bob": "bob123",
}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def initialize_database():
    with sqlite3.connect(DB_NAME) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                display_name TEXT NOT NULL,
                email TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        for username, password in USERS.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO users
                (username, password_hash)
                VALUES (?, ?)
                """,
                (username, hash_password(password))
            )

        # Seed profiles only if they are not already present.
        conn.execute("""
            INSERT OR IGNORE INTO profiles
            (id, user_id, display_name, email)
            VALUES (1, 1, 'Alice', 'alice@example.test')
        """)

        conn.execute("""
            INSERT OR IGNORE INTO profiles
            (id, user_id, display_name, email)
            VALUES (2, 2, 'Bob', 'bob@example.test')
        """)


class AuthLabHandler(BaseHTTPRequestHandler):

    def send_json(self, status, data, extra_headers=None):

        body = json.dumps(data, indent=2).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        if extra_headers:
            for name, value in extra_headers:
                self.send_header(name, value)

        self.end_headers()
        self.wfile.write(body)

    def get_session_user(self):

        cookie_header = self.headers.get("Cookie", "")

        cookies = SimpleCookie()

        try:
            cookies.load(cookie_header)
        except Exception:
            return None

        if "session" not in cookies:
            return None

        token = cookies["session"].value

        session = SESSIONS.get(token)

        if not session:
            return None

        user_id, expires_at = session

        if time.time() >= expires_at:
            SESSIONS.pop(token, None)
            return None

        return user_id

    def do_POST(self):

        parsed = urlparse(self.path)

        if parsed.path == "/login":
            self.handle_login()
            return

        if parsed.path == "/logout":
            self.handle_logout()
            return

        self.send_json(
            404,
            {"error": "Route not found"}
        )

    def handle_login(self):

        length = int(
            self.headers.get("Content-Length", "0")
        )

        if length > 4096:
            self.send_json(
                413,
                {"error": "Request too large"}
            )
            return

        raw_body = self.rfile.read(length).decode(
            "utf-8",
            errors="replace"
        )

        params = parse_qs(raw_body)

        username = params.get(
            "username",
            [""]
        )[0]

        password = params.get(
            "password",
            [""]
        )[0]

        if not username or not password:
            self.send_json(
                400,
                {
                    "error":
                    "Username and password required"
                }
            )
            return

        with sqlite3.connect(DB_NAME) as conn:

            row = conn.execute(
                """
                SELECT id, password_hash
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

        supplied_hash = hash_password(password)

        if not row or not hmac.compare_digest(
            supplied_hash,
            row[1]
        ):
            self.send_json(
                401,
                {
                    "error":
                    "Invalid username or password"
                }
            )
            return

        # Issue a fresh random session token.
        token = secrets.token_urlsafe(32)

        user_id = row[0]

        SESSIONS[token] = (
            user_id,
            time.time() + SESSION_TTL
        )

        self.send_json(
            200,
            {
                "message": "Login successful",
                "username": username
            },
            extra_headers=[
                (
                    "Set-Cookie",
                    f"session={token}; "
                    f"HttpOnly; "
                    f"SameSite=Strict; "
                    f"Path=/; "
                    f"Max-Age={SESSION_TTL}"
                )
            ]
        )

    def handle_logout(self):

        cookie_header = self.headers.get(
            "Cookie",
            ""
        )

        cookies = SimpleCookie()

        try:
            cookies.load(cookie_header)
        except Exception:
            cookies = SimpleCookie()

        if "session" in cookies:

            token = cookies["session"].value

            SESSIONS.pop(token, None)

        self.send_json(
            200,
            {
                "message": "Logged out"
            },
            extra_headers=[
                (
                    "Set-Cookie",
                    "session=; "
                    "HttpOnly; "
                    "SameSite=Strict; "
                    "Path=/; "
                    "Max-Age=0"
                )
            ]
        )

    def do_GET(self):

        parsed = urlparse(self.path)

        if parsed.path == "/":

            self.send_json(
                200,
                {
                    "message": "Auth lab",
                    "routes": [
                        "POST /login",
                        "GET /me",
                        "GET /profile?id=1",
                        "POST /logout"
                    ]
                }
            )

            return

        if parsed.path == "/me":
            self.handle_me()
            return

        if parsed.path == "/profile":
            self.handle_profile()
            return

        self.send_json(
            404,
            {"error": "Route not found"}
        )

    def handle_me(self):

        user_id = self.get_session_user()

        if user_id is None:
            self.send_json(
                401,
                {"error": "Login required"}
            )
            return

        with sqlite3.connect(DB_NAME) as conn:

            row = conn.execute(
                """
                SELECT username
                FROM users
                WHERE id = ?
                """,
                (user_id,)
            ).fetchone()

        if not row:
            self.send_json(
                401,
                {"error": "Invalid session"}
            )
            return

        self.send_json(
            200,
            {
                "user_id": user_id,
                "username": row[0]
            }
        )

    def handle_profile(self):

        user_id = self.get_session_user()

        if user_id is None:
            self.send_json(
                401,
                {"error": "Login required"}
            )
            return

        params = parse_qs(
            urlparse(self.path).query
        )

        profile_id = params.get(
            "id",
            [""]
        )[0]

        if not profile_id.isdigit():
            self.send_json(
                400,
                {
                    "error":
                    "A numeric profile id is required"
                }
            )
            return

        # INTENTIONALLY VULNERABLE:
        #
        # The application verifies that the user is logged in,
        # but it does NOT verify that the requested profile
        # belongs to the logged-in user.
        #
        # Therefore Alice can request profile?id=2
        # and access Bob's profile.

        query = """
            SELECT id, user_id, display_name, email
            FROM profiles
            WHERE id = ? AND user_id = ?
        """

        with sqlite3.connect(DB_NAME) as conn:
            row = conn.execute(
            query,
            (int(profile_id), user_id)
            ).fetchone()

        if not row:
            self.send_json(
                404,
                {"error": "Profile not found"}
            )
            return

        self.send_json(
            200,
            {
                "id": row[0],
                "user_id": row[1],
                "display_name": row[2],
                "email": row[3]
            }
        )

    def log_message(self, format, *args):
        print("[HTTP]", format % args)


if __name__ == "__main__":

    initialize_database()

    server = HTTPServer(
        (HOST, PORT),
        AuthLabHandler
    )

    print(
        f"Auth lab running at "
        f"http://{HOST}:{PORT}"
    )

    print(
        "Demo users: "
        "alice / alice123, "
        "bob / bob123"
    )

    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nServer stopped.")

    finally:
        server.server_close()