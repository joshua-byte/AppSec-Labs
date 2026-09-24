# Blind SQL Injection

## Overview

This lab demonstrates Boolean-based Blind SQL Injection using a deliberately vulnerable Python HTTP server with SQLite.

Unlike a traditional SQL Injection response, the application does not return database records directly. Instead, it exposes only a Boolean result indicating whether a username exists.

The lab covers:

- Vulnerable SQL query construction
- Boolean-based Blind SQL Injection
- True/false response comparison
- Root-cause analysis
- Parameterized SQL queries
- Remediation
- Verification

## Environment

- Python 3
- SQLite
- Burp Suite
- Local HTTP server
- Host: `127.0.0.1`
- Port: `8003`

## Application Endpoint

```text
GET /check-user?username=<username>
```

Example:

```text
http://127.0.0.1:8003/check-user?username=alice
```

## Vulnerable Implementation

The vulnerable application directly concatenated user-controlled input into the SQL query:

```python
query = f"""
    SELECT id
    FROM users
    WHERE username = '{username}'
"""
```

The application then returned only whether a matching row existed:

```python
self.send_json(
    200,
    {"exists": row is not None}
)
```

This Boolean response creates an observable true/false condition that can be used to demonstrate Blind SQL Injection.

## Baseline Testing

A legitimate username was first tested:

```text
username=alice
```

Expected response:

```json
{
  "exists": true
}
```

A non-existent username was then tested:

```text
username=doesnotexist
```

Expected response:

```json
{
  "exists": false
}
```

These responses established the application's normal Boolean behavior.

## Boolean Blind SQL Injection Demonstration

The vulnerable application was tested with Boolean conditions through the `username` parameter.

### TRUE Condition

Payload:

```text
alice' OR '1'='1
```

The condition evaluates to true and changes the SQL query logic.

The application returned:

```json
{
  "exists": true
}
```

### FALSE Condition

Payload:

```text
alice' AND '1'='2
```

The condition evaluates to false.

The application returned:

```json
{
  "exists": false
}
```

The difference between the true and false responses demonstrates Boolean-based Blind SQL Injection.

## Root Cause

The vulnerability was caused by directly concatenating untrusted input into the SQL query:

```python
WHERE username = '{username}'
```

Because the input was interpreted as part of the SQL statement, Boolean expressions supplied by the requester could alter the query's behavior.

The application did not need to expose database records or SQL errors for the vulnerability to be observable. The Boolean `exists` response provided the required signal.

## Remediation

The vulnerable query was replaced with a parameterized query:

```python
query = """
    SELECT id
    FROM users
    WHERE username = ?
"""
```

The username is passed separately:

```python
row = conn.execute(
    query,
    (username,)
).fetchone()
```

This causes the supplied value to be treated as data rather than executable SQL syntax.

## Verification

After remediation, the application was tested again.

### Legitimate Request

```text
username=alice
```

Expected:

```json
{
  "exists": true
}
```

### Previous TRUE Payload

```text
alice' OR '1'='1
```

Expected:

```json
{
  "exists": false
}
```

### Previous FALSE Payload

```text
alice' AND '1'='2
```

Expected:

```json
{
  "exists": false
}
```

The legitimate username continued to work, while the previous SQL injection payloads were treated as username values rather than SQL syntax.


## Security Concepts Demonstrated

- Blind SQL Injection
- Boolean-based SQL Injection
- SQL query manipulation
- Input handling
- Parameterized queries
- Vulnerability verification
