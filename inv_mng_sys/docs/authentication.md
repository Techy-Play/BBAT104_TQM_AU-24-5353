# Local Authentication & Security Specification

## Overview

The Inventory Management System (IMS) provides an offline, local-only authentication and session management layer. It protects inventory records and user settings without requiring an Internet connection, third-party authentication services, or cloud infrastructure.

---

## 1. Authentication Flow Diagram

```text
Application Launch
        │
        ▼
Check Local SQLite Database
        │
        ├─── No User ────► First-Run Setup Screen
        │                         │
        │                         ▼
        │                  Create Account (PBKDF2 Salted Hash)
        │                         │
        │                         ▼
        │                  Dashboard (Profile Active)
        │
        └─── User Exists ─► Check Session State
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                    Valid Session      No Session / Expired
                         │                 │
                         ▼                 ▼
                     Dashboard        Login Screen
                                           │
                                           ▼
                                      Verify Credentials
                                           │
                                           ▼
                                       Dashboard
```

---

## 2. First-Run Setup Wizard (`app/authentication/setup.py`)

When the application is launched for the very first time, `is_first_run()` queries SQLite:
```sql
SELECT 1 FROM users LIMIT 1;
```
If no record exists, the user is presented with the First-Run Setup wizard.

### Collected Data & Validation:
- **User / Full Name**: Minimum 2 characters. Stored in `users.full_name` and displayed on the dashboard greeting.
- **Store / Warehouse / Business Name**: Minimum 2 characters. Stored in `users.organization_name` and displayed in the application header.
- **Username**: 3–30 alphanumeric characters, hyphens, periods, or underscores. Case-insensitive uniqueness enforced via SQLite `COLLATE NOCASE` and `UNIQUE` constraint.
- **Password**: Minimum 6 characters. Must match the confirmation field.
- **Keep Me Logged In**: Optional boolean preference for session persistence.

---

## 3. Cryptographic Security & Password Hashing (`app/authentication/security.py`)

No plaintext passwords are ever stored, logged, or retained in memory:

1. **Unique Cryptographic Salt**:
   Each user receives a unique 32-character hexadecimal salt generated via `secrets.token_hex(16)`.
2. **PBKDF2-HMAC-SHA256**:
   Key derivation executes 100,000 iterations using Python's standard library `hashlib.pbkdf2_hmac`.
3. **Constant-Time Verification**:
   Password verification uses `hmac.compare_digest(computed_hash, stored_hash)` to protect against timing side-channel attacks.

---

## 4. Session Management & "Keep Me Logged In" (`app/authentication/login.py`)

### Offline Token Architecture:
- Plaintext credentials are **never** stored in files or settings.
- When **Keep Me Logged In** is enabled:
  1. A cryptographically random 64-character token is generated via `secrets.token_hex(32)`.
  2. The token is stored in the `users` table (`session_token`) alongside `keep_logged_in = 1`.
  3. The token is registered in `app_settings` under the key `active_session_token`.
- On startup, `restore_session()` validates the active token against SQLite. If valid, the user enters directly into the dashboard.

### Logout & Session Invalidation:
- Clicking **Log Out** immediately executes `logout_user()`:
  - Sets `users.session_token = NULL` and `users.keep_logged_in = 0`.
  - Clears `active_session_token` in `app_settings`.
  - Transitions the UI back to the login screen.

---

## 5. Security & Privacy Decisions

| Security Goal | Implementation Mechanism |
|---|---|
| Offline Integrity | Fully self-contained; uses Python standard library `secrets`, `hashlib`, `hmac`. |
| Credential Protection | Salted PBKDF2 with 100,000 iterations. Plaintext passwords never written to disk. |
| User Enumeration Defense | Generic error message (`"Invalid username or password."`) on failed login. |
| Timing Attack Defense | `hmac.compare_digest` for hash verification. |
| Parameter Injection Defense | 100% parameterized SQL queries via SQLite DB layer. |

---

## 6. Relevant Modules

- `app/authentication/security.py`: Cryptographic primitives, salts, hashes, and `UserSession` model.
- `app/authentication/setup.py`: First-run detection, validation, and account provisioning.
- `app/authentication/login.py`: Credential verification, session restoration, and logout.
- `app/settings/settings.py`: Profile updates, password changes, and preference toggles.
- `app/ui/views_auth.py`: CustomTkinter GUI forms for Setup and Login.
