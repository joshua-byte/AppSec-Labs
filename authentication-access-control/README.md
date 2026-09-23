# Authentication & Access Control Lab

A local application security lab focused on authentication, session management, cookies, and broken access control.

The lab uses a Python HTTP server with SQLite as the backend and Burp Suite for security testing.

---

## Objectives

- Understand basic web authentication
- Understand server-side session management
- Inspect authentication cookies
- Test authenticated endpoints
- Identify an IDOR vulnerability
- Understand the difference between authentication and authorization
- Remediate the access control vulnerability
- Verify that the fix prevents unauthorized access

---

## Lab Environment

- Python 3
- SQLite
- Burp Suite
- Local HTTP server
- Host: `127.0.0.1`
- Port: `8004`

---

## Demo Accounts

```text
Alice
Username: alice
Password: alice123

Bob
Username: bob
Password: bob123
