"""First-run setup logic and initial user registration.

Detects if the application is running for the first time, validates
required onboarding parameters, and provisions the initial local administrator account.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional, Union

from app.authentication.security import (
    UserSession,
    generate_salt,
    generate_session_token,
    hash_password,
)
from app.database.connection import get_db_connection
from app.database.queries import execute_insert, fetch_one, set_setting

logger = logging.getLogger(__name__)

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{3,30}$")
MIN_PASSWORD_LENGTH = 6


def is_first_run(custom_path: Optional[Union[str, Path]] = None) -> bool:
    """Return True if no user accounts exist in the database."""
    sql = "SELECT 1 FROM users LIMIT 1;"
    row = fetch_one(sql, custom_path=custom_path)
    return row is None


def validate_setup_data(
    full_name: str,
    org_name: str,
    username: str,
    password: str,
    confirm_password: str,
) -> Optional[str]:
    """Validate user registration inputs. Returns error message or None if valid."""
    cleaned_full_name = full_name.strip()
    cleaned_org = org_name.strip()
    cleaned_username = username.strip()

    if not cleaned_full_name:
        return "Please enter your Full Name."
    if len(cleaned_full_name) < 2:
        return "Full Name must be at least 2 characters long."

    if not cleaned_org:
        return "Please enter your Store / Warehouse / Business Name."
    if len(cleaned_org) < 2:
        return "Store / Warehouse / Business Name must be at least 2 characters long."

    if not cleaned_username:
        return "Please enter a Username."
    if not USERNAME_REGEX.match(cleaned_username):
        return "Username must be 3-30 characters long and contain only letters, numbers, hyphens, periods, or underscores."

    if not password:
        return "Please enter a Password."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    if password != confirm_password:
        return "Passwords do not match. Please re-enter."

    return None


def register_first_user(
    full_name: str,
    org_name: str,
    username: str,
    password: str,
    confirm_password: str,
    keep_logged_in: bool = False,
    custom_path: Optional[Union[str, Path]] = None,
) -> UserSession:
    """Create the initial application user account.
    
    Raises:
        ValueError: If validation fails or username is already taken.
    """
    validation_err = validate_setup_data(
        full_name=full_name,
        org_name=org_name,
        username=username,
        password=password,
        confirm_password=confirm_password,
    )
    if validation_err:
        raise ValueError(validation_err)

    cleaned_username = username.strip()
    cleaned_full_name = full_name.strip()
    cleaned_org = org_name.strip()

    # Verify username uniqueness
    existing = fetch_one(
        "SELECT id FROM users WHERE username = ? COLLATE NOCASE;",
        (cleaned_username,),
        custom_path=custom_path,
    )
    if existing:
        raise ValueError(f"Username '{cleaned_username}' is already taken.")

    # Cryptographically secure password hash with unique salt
    salt = generate_salt()
    pwd_hash = hash_password(password, salt)
    session_token = generate_session_token() if keep_logged_in else None
    keep_val = 1 if keep_logged_in else 0

    sql = """
    INSERT INTO users (username, password_hash, salt, full_name, organization_name, keep_logged_in, session_token)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    user_id = execute_insert(
        sql,
        (
            cleaned_username,
            pwd_hash,
            salt,
            cleaned_full_name,
            cleaned_org,
            keep_val,
            session_token,
        ),
        custom_path=custom_path,
    )

    if keep_logged_in and session_token:
        set_setting("active_session_token", session_token, custom_path=custom_path)
    else:
        set_setting("active_session_token", "", custom_path=custom_path)

    logger.info("Successfully provisioned initial user '%s' (ID: %d)", cleaned_username, user_id)

    return UserSession(
        id=user_id,
        username=cleaned_username,
        full_name=cleaned_full_name,
        organization_name=cleaned_org,
        keep_logged_in=keep_logged_in,
        session_token=session_token,
    )
