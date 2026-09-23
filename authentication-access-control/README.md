# Authentication & Access Control Lab

## Overview

A local Python/SQLite application security lab covering authentication, session management, and IDOR (Insecure Direct Object Reference).

## Environment

- Python 3
- SQLite
- Burp Suite
- Localhost: `127.0.0.1:8004`

## Authentication

The application provides login functionality for two test users:

- Alice
- Bob

Successful authentication creates a server-side session associated with the authenticated user's ID.

The session cookie uses:

- `HttpOnly`
- `SameSite=Strict`
- `Max-Age=1800`

## IDOR Vulnerability

The vulnerable application allowed an authenticated user to access another user's profile by changing the profile ID.

Example:

```http
GET /profile?id=2
```

While authenticated as Alice, this request returned Bob's profile.

### Root Cause

The application checked whether the requested profile existed but did not verify that the profile belonged to the authenticated user.

## Remediation

The database query was changed from checking only the profile ID:

```python
WHERE id = ?
```

to checking both the profile ID and authenticated user ID:

```python
WHERE id = ? AND user_id = ?
```

The authenticated user's ID is passed to the query:

```python
(int(profile_id), user_id)
```

## Verification

After the fix:

- Alice can access her own profile.
- Alice cannot access Bob's profile.
- Unauthorized access returns `Profile not found`.

## Evidence

Screenshots documenting the testing, IDOR exploitation, remediation, and verification are included in the `screenshots/` directory.

## Files

```text
04-authentication-access-control/
├── auth_lab.py
├── README.md
└── screenshots/
```

## Disclaimer

This application is intentionally vulnerable and is intended only for local security training.
