# SQL Injection Lab

## Overview

A local Python/SQLite application security lab covering SQL Injection, Boolean-based testing, and secure SQL query remediation.

## Environment

- Python 3
- SQLite
- Burp Suite
- Localhost: `127.0.0.1:8001`

## Application

The application exposes:

```http
GET /user?username=<username>
```

The database contains three training users:

- Alice
- Bob
- Charlie

## SQL Injection Vulnerability

The vulnerable version directly inserted the `username` parameter into the SQL query.

A Boolean-based payload was used to demonstrate the vulnerability:

```text
alice' OR '1'='1
```

The true condition caused the application to return multiple database records.

A false Boolean condition:

```text
alice' OR '1'='2
```

did not return the same records.

This demonstrated that user-controlled input was being interpreted as part of the SQL statement.

## Root Cause

The vulnerable implementation constructed SQL using user-controlled input instead of separating SQL code from data.

## Remediation

The query was changed to use a parameterized statement:

```python
query = """
    SELECT id, username, email
    FROM users
    WHERE username = ?
"""
```

The username is then supplied separately:

```python
rows = conn.execute(
    query,
    (username,)
).fetchall()
```

This causes the complete input to be treated as a parameter value rather than executable SQL syntax.

## Verification

The same SQL injection payload used against the vulnerable application was tested again after remediation.

The payload was treated as a username value and did not return all database records.

A normal lookup such as:

```http
GET /user?username=alice
```

continues to return Alice's record.

## Evidence

Screenshots documenting the vulnerable testing and remediation process are included in the `screenshots/` directory.

## Files

```text
01-sql-injection/
├── sql_lab.py
├── README.md
└── screenshots/
```

## Disclaimer

This application is intentionally vulnerable and is intended only for local security training.

