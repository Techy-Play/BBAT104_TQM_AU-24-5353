"""Settings service layer preparing for Phase 5 & 10.

Provides programmatic interfaces to update user profiles,
toggle Keep Me Logged In preferences, and update credentials.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.authentication.login import (
    change_user_password,
    get_user_profile,
    update_keep_logged_in_preference,
    update_user_profile,
)
from app.authentication.security import UserSession

logger = logging.getLogger(__name__)


class SettingsService:
    """Service handling profile and security configuration updates."""

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
