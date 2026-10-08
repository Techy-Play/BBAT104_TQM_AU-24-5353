"""Authentication, session restoration, and credential verification.

Implements:
- Constant-time password verification against salted PBKDF2 hash.
- Safe generic error responses to prevent user enumeration.
- Secure local session tokens for "Keep Me Logged In".
- Session restoration on application launch.
- Session invalidation on logout.
- Profile update and password modification routines for Settings.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

from app.authentication.security import (
    UserSession,
    generate_salt,
    generate_session_token,
    hash_password,
    verify_password,
)
from app.database.connection import get_db_connection
from app.database.queries import (
    execute_update_or_delete,
    fetch_one,
    get_setting,
    set_setting,
)

logger = logging.getLogger(__name__)


def authenticate_user(
    username: str,
    password: str,
    keep_logged_in: bool = False,
    custom_path: Optional[Union[str, Path]] = None,
) -> UserSession:
    """Authenticate credentials against SQLite records.
    
    Raises:
        ValueError: If username or password is invalid or missing.
    """
    cleaned_username = username.strip()
    if not cleaned_username or not password:
        raise ValueError("Invalid username or password.")

    sql = """
    SELECT id, username, password_hash, salt, full_name, organization_name, keep_logged_in, session_token
    FROM users
    WHERE username = ? COLLATE NOCASE;
    """
    row = fetch_one(sql, (cleaned_username,), custom_path=custom_path)
    if not row:
        logger.warning("Authentication failed: user '%s' not found.", cleaned_username)
        raise ValueError("Invalid username or password.")

    if not verify_password(password, row["password_hash"], row["salt"]):
        logger.warning("Authentication failed: invalid password for user '%s'.", cleaned_username)
        raise ValueError("Invalid username or password.")

    user_id = row["id"]
    if keep_logged_in:
        token = generate_session_token()
        execute_update_or_delete(
            "UPDATE users SET keep_logged_in = 1, session_token = ? WHERE id = ?;",
            (token, user_id),
            custom_path=custom_path,
        )
        set_setting("active_session_token", token, custom_path=custom_path)
    else:
        token = None
        execute_update_or_delete(
            "UPDATE users SET keep_logged_in = 0, session_token = NULL WHERE id = ?;",
            (user_id,),
            custom_path=custom_path,
        )
        set_setting("active_session_token", "", custom_path=custom_path)

    logger.info("User '%s' authenticated successfully (keep_logged_in=%s).", cleaned_username, keep_logged_in)

    return UserSession(
        id=user_id,
        username=row["username"],
        full_name=row["full_name"],
        organization_name=row["organization_name"],
        keep_logged_in=keep_logged_in,
        session_token=token,
    )


def restore_session(
    custom_path: Optional[Union[str, Path]] = None,
) -> Optional[UserSession]:
    """Attempt to restore an existing authenticated local session."""
    active_token = get_setting("active_session_token", default="", custom_path=custom_path)
    if not active_token:
        return None

    sql = """
    SELECT id, username, full_name, organization_name, keep_logged_in, session_token
    FROM users
    WHERE session_token = ? AND keep_logged_in = 1;
    """
    row = fetch_one(sql, (active_token,), custom_path=custom_path)
    if not row:
        logger.info("Invalid or stale session token detected. Clearing active session.")
        set_setting("active_session_token", "", custom_path=custom_path)
        return None

    logger.info("Session restored successfully for user '%s'.", row["username"])
    return UserSession(
        id=row["id"],
        username=row["username"],
        full_name=row["full_name"],
        organization_name=row["organization_name"],
        keep_logged_in=True,
        session_token=row["session_token"],
    )


def logout_user(
    user_id: int,
    custom_path: Optional[Union[str, Path]] = None,
) -> None:
    """Invalidate session token and clear active session on logout."""
    execute_update_or_delete(
        "UPDATE users SET session_token = NULL, keep_logged_in = 0 WHERE id = ?;",
        (user_id,),
        custom_path=custom_path,
    )
    set_setting("active_session_token", "", custom_path=custom_path)
    logger.info("User ID %d logged out. Session invalidated.", user_id)


def get_user_profile(
    user_id: int,
    custom_path: Optional[Union[str, Path]] = None,
) -> Optional[UserSession]:
    """Retrieve the current user profile from the database."""
    sql = """
    SELECT id, username, full_name, organization_name, keep_logged_in, session_token
    FROM users
    WHERE id = ?;
    """
    row = fetch_one(sql, (user_id,), custom_path=custom_path)
    if not row:
        return None
    return UserSession(
        id=row["id"],
        username=row["username"],
        full_name=row["full_name"],
        organization_name=row["organization_name"],
        keep_logged_in=bool(row["keep_logged_in"]),
        session_token=row["session_token"],
    )


def update_user_profile(
    user_id: int,
    full_name: str,
    org_name: str,
    custom_path: Optional[Union[str, Path]] = None,
) -> UserSession:
    """Update user full name and organization name."""
    cleaned_name = full_name.strip()
    cleaned_org = org_name.strip()
    if not cleaned_name or len(cleaned_name) < 2:
        raise ValueError("Full Name must be at least 2 characters long.")
    if not cleaned_org or len(cleaned_org) < 2:
        raise ValueError("Store / Warehouse / Business Name must be at least 2 characters long.")

    rows_affected = execute_update_or_delete(
        "UPDATE users SET full_name = ?, organization_name = ? WHERE id = ?;",
        (cleaned_name, cleaned_org, user_id),
        custom_path=custom_path,
    )
    if rows_affected == 0:
        raise ValueError("User not found.")

    profile = get_user_profile(user_id, custom_path=custom_path)
    if not profile:
        raise ValueError("Could not retrieve updated user profile.")
    return profile


def update_keep_logged_in_preference(
    user_id: int,
    keep_logged_in: bool,
    custom_path: Optional[Union[str, Path]] = None,
) -> UserSession:
    """Change the Keep Me Logged In preference for a user."""
    if keep_logged_in:
        token = generate_session_token()
        execute_update_or_delete(
            "UPDATE users SET keep_logged_in = 1, session_token = ? WHERE id = ?;",
            (token, user_id),
            custom_path=custom_path,
        )
        set_setting("active_session_token", token, custom_path=custom_path)
    else:
        execute_update_or_delete(
            "UPDATE users SET keep_logged_in = 0, session_token = NULL WHERE id = ?;",
            (user_id,),
            custom_path=custom_path,
        )
        set_setting("active_session_token", "", custom_path=custom_path)

    profile = get_user_profile(user_id, custom_path=custom_path)
    if not profile:
        raise ValueError("User profile not found.")
    return profile


def change_user_password(
    user_id: int,
    current_password: str,
    new_password: str,
    confirm_new_password: str,
    custom_path: Optional[Union[str, Path]] = None,
) -> None:
    """Verify existing password and set new hashed password."""
    if not current_password:
        raise ValueError("Current password is required.")
    if not new_password or len(new_password) < 6:
        raise ValueError("New password must be at least 6 characters long.")
    if new_password != confirm_new_password:
        raise ValueError("New passwords do not match.")

    row = fetch_one("SELECT password_hash, salt FROM users WHERE id = ?;", (user_id,), custom_path=custom_path)
    if not row:
        raise ValueError("User not found.")

    if not verify_password(current_password, row["password_hash"], row["salt"]):
        raise ValueError("Current password is incorrect.")

    new_salt = generate_salt()
    new_hash = hash_password(new_password, new_salt)

    execute_update_or_delete(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?;",
        (new_hash, new_salt, user_id),
        custom_path=custom_path,
    )
    logger.info("Password changed successfully for user ID %d.", user_id)
