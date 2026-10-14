"""Settings service layer for user profiles, session preferences, and theme configuration.

Provides programmatic interfaces to update user profiles,
toggle Keep Me Logged In preferences, update credentials,
and persist UI theme preferences across application sessions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

from app.authentication.login import (
    change_user_password,
    get_user_profile,
    update_keep_logged_in_preference,
    update_user_profile,
)
from app.authentication.security import UserSession
from app.database.queries import execute_update_or_delete, fetch_one

logger = logging.getLogger(__name__)


class SettingsService:
    """Service handling profile, security, and persistent theme configuration."""

    @staticmethod
    def get_profile(user_id: int) -> Optional[UserSession]:
        """Fetch current user profile."""
        return get_user_profile(user_id)

    @staticmethod
    def update_profile(user_id: int, full_name: str, organization_name: str) -> UserSession:
        """Update full name and organization name."""
        return update_user_profile(user_id, full_name, organization_name)

    @staticmethod
    def update_session_preference(user_id: int, keep_logged_in: bool) -> UserSession:
        """Update Keep Me Logged In preference."""
        return update_keep_logged_in_preference(user_id, keep_logged_in)

    @staticmethod
    def change_password(
        user_id: int,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> None:
        """Change user password after verifying existing credentials."""
        change_user_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password,
            confirm_new_password=confirm_password,
        )

    @staticmethod
    def get_theme_preference(custom_path: Optional[Union[str, Path]] = None) -> str:
        """Fetch persistent theme setting from app_settings ('system', 'dark', 'light').
        Defaults to 'system' (device default) if not explicitly set.
        """
        try:
            row = fetch_one(
                "SELECT value FROM app_settings WHERE key = 'theme';",
                custom_path=custom_path,
            )
            if row and row["value"]:
                val = str(row["value"]).strip().lower()
                if val in ("system", "dark", "light"):
                    return val
        except Exception as exc:
            logger.warning("Could not read theme preference from database: %s", exc)
        return "system"

    @staticmethod
    def set_theme_preference(theme: str, custom_path: Optional[Union[str, Path]] = None) -> str:
        """Persist theme setting into app_settings table ('system', 'dark', 'light')."""
        val = str(theme).strip().lower()
        if val not in ("system", "dark", "light"):
            val = "system"
        try:
            execute_update_or_delete(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES ('theme', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
                """,
                (val,),
                custom_path=custom_path,
            )
            logger.info("Persisted theme preference '%s' in database.", val)
        except Exception as exc:
            logger.error("Failed to persist theme preference: %s", exc)
        return val
