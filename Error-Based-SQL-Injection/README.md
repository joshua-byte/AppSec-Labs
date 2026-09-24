
# Error-Based SQL Injection

## Overview

This lab demonstrates Error-Based SQL Injection and database error information disclosure using a deliberately vulnerable Python HTTP server with SQLite.

## Environment

- Python 3
- SQLite
- Burp Suite
- Local HTTP server
- Host: `127.0.0.1`
- Port: `8002`

## Application Endpoint

```text
GET /user?username=<username>
```

Example:

```text
http://127.0.0.1:8002/user?username=alice
```

## Vulnerable Implementation

The vulnerable application directly concatenated user-controlled input into the SQL query:

```python
query = f"""
    SELECT id, username, email
    FROM users
    WHERE username = '{username}'
"""
```

The application also returned the database exception to the client:

```python
except sqlite3.Error as e:
    self.send_json(
        500,
        {
            "error": "Database error",
            "details": str(e)
        }
    )
```

## Baseline Test

A normal request was first sent to confirm that the application was functioning correctly:

```http
GET /user?username=alice
```

Expected response:

```json
{
  "users": [
    {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com"
    }
  ]
}
```

## Error-Based SQL Injection Demonstration

A malformed input was supplied through the `username` parameter:

```text
alice'''
```

The resulting SQL statement became malformed because the input was directly inserted into the query.

The application returned a database error to the client, demonstrating database error information disclosure.

## Root Cause

The vulnerability had two primary causes:

### Unsafe SQL Construction

User-controlled input was concatenated directly into the SQL statement:

```python
WHERE username = '{username}'
```

### Excessive Error Disclosure

The application returned:

```python
str(e)
```

directly to the client.

## Remediation

### Parameterized SQL Query

The vulnerable query was replaced with:

```python
query = """
    SELECT id, username, email
    FROM users
    WHERE username = ?
"""
```

The input is supplied separately:

```python
rows = conn.execute(
    query,
    (username,)
).fetchall()
```

This prevents the supplied username from being interpreted as SQL syntax.

### Secure Error Handling

Database errors are handled server-side:

```python
except sqlite3.Error:
    logging.exception("Database query failed")

    self.send_json(
        500,
        {"error": "Internal server error"}
    )
```

The detailed exception is logged on the server instead of being returned to the client.

## Verification

After remediation:

- Normal username queries continued to work.
- The previous malformed input was no longer interpreted as SQL syntax.
- Database error details were no longer exposed to the client.

This verified both remediation measures:

- Parameterized SQL query
- Generic client-facing error response


## Security Concepts Demonstrated

- SQL Injection
- Error-Based SQL Injection
- Input handling
- Parameterized queries
- Database error disclosure
- Secure exception handling
- Vulnerability verification

