"""Offline security, password hashing, and session token utilities.

Uses Python standard library cryptography (hashlib, hmac, secrets):
- PBKDF2-HMAC-SHA256 with 100,000 iterations for secure password hashing.
- Unique cryptographically random salt per user (secrets.token_hex).
- Constant-time string comparison (hmac.compare_digest) to prevent timing attacks.
- Cryptographically secure random session tokens.
- Fully offline with zero external network or service dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional

PBKDF2_ITERATIONS = 100_000
HASH_ALGORITHM = "sha256"


@dataclass(frozen=True)
class UserSession:
    """Immutable representation of an authenticated user profile and session state."""

    id: int
    username: str
    full_name: str
    organization_name: str
    keep_logged_in: bool
    session_token: Optional[str] = None

    def display_greeting(self) -> str:
        """Formatted greeting for the dashboard and UI."""
        return f"Welcome, {self.full_name}"

    def display_org(self) -> str:
        """Formatted organization or store title."""
        return self.organization_name


def generate_salt() -> str:
    """Generate a cryptographically secure random hexadecimal salt (32 chars / 16 bytes)."""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """Derive a salted PBKDF2-HMAC-SHA256 hash from a plaintext password."""
    if not password:
        raise ValueError("Password cannot be empty.")
    if not salt:
        raise ValueError("Salt cannot be empty.")

    key = hashlib.pbkdf2_hmac(
        hash_name=HASH_ALGORITHM,
        password=password.encode("utf-8"),
        salt=salt.encode("utf-8"),
        iterations=PBKDF2_ITERATIONS,
    )
    return key.hex()


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify an input password against stored hash using constant-time comparison."""
    if not password or not stored_hash or not salt:
        return False
    computed_hash = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, stored_hash)


def generate_session_token() -> str:
    """Generate a cryptographically secure 64-character random session token."""
    return secrets.token_hex(32)
