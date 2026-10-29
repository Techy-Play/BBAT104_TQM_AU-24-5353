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
from app.authentication.security import UserSession, verify_password
from app.database.connection import get_db_connection
from app.database.queries import execute_update_or_delete, fetch_one

logger = logging.getLogger(__name__)

CURRENCY_INR = "INR"
CURRENCY_USD = "USD"
DEFAULT_CURRENCY = CURRENCY_INR
EXCHANGE_RATE_USD_INR = 83.0  # Standard exchange rate: 1 USD = 83.00 INR

CURRENCY_OPTIONS = [
    "Rupees (₹)",
    "USD ($)",
]

CURRENCY_DISPLAY_TO_CODE = {
    "Rupees (₹)": CURRENCY_INR,
    "USD ($)": CURRENCY_USD,
}

CURRENCY_CODE_TO_DISPLAY = {
    CURRENCY_INR: "Rupees (₹)",
    CURRENCY_USD: "USD ($)",
}

CURRENCY_SYMBOLS = {
    CURRENCY_INR: "₹",
    CURRENCY_USD: "$",
}


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

    @staticmethod
    def get_currency_preference(custom_path: Optional[Union[str, Path]] = None) -> str:
        """Fetch persistent currency setting from app_settings ('INR', 'USD').
        Defaults to 'INR' (Rupees) if not explicitly set.
        """
        try:
            row = fetch_one(
                "SELECT value FROM app_settings WHERE key = 'currency';",
                custom_path=custom_path,
            )
            if row and row["value"]:
                val = str(row["value"]).strip().upper()
                if val in (CURRENCY_INR, CURRENCY_USD):
                    return val
                if "RUPEE" in val or "INR" in val or "₹" in val:
                    return CURRENCY_INR
                if "USD" in val or "$" in val:
                    return CURRENCY_USD
        except Exception as exc:
            logger.warning("Could not read currency preference from database: %s", exc)
        return DEFAULT_CURRENCY

    @staticmethod
    def set_currency_preference(
        currency: str,
        custom_path: Optional[Union[str, Path]] = None,
        convert_prices: bool = True,
    ) -> str:
        """Persist currency setting into app_settings table ('INR' or 'USD').

        When switching between INR and USD, converts all existing product prices
        proportionately using the standard exchange rate (1 USD = 83 INR).
        """
        old_code = SettingsService.get_currency_preference(custom_path=custom_path)

        code = str(currency).strip().upper()
        if currency in CURRENCY_DISPLAY_TO_CODE:
            code = CURRENCY_DISPLAY_TO_CODE[currency]
        elif code not in (CURRENCY_INR, CURRENCY_USD):
            code = DEFAULT_CURRENCY

        if convert_prices and old_code != code:
            try:
                if old_code == CURRENCY_INR and code == CURRENCY_USD:
                    # 1 USD = 83 INR -> price_usd = price_inr / 83.0
                    execute_update_or_delete(
                        "UPDATE products SET price = ROUND(price / ?, 2);",
                        (EXCHANGE_RATE_USD_INR,),
                        custom_path=custom_path,
                    )
                    logger.info(
                        "Converted product prices from INR to USD (divided by %s).",
                        EXCHANGE_RATE_USD_INR,
                    )
                elif old_code == CURRENCY_USD and code == CURRENCY_INR:
                    # price_inr = price_usd * 83.0
                    execute_update_or_delete(
                        "UPDATE products SET price = ROUND(price * ?, 2);",
                        (EXCHANGE_RATE_USD_INR,),
                        custom_path=custom_path,
                    )
                    logger.info(
                        "Converted product prices from USD to INR (multiplied by %s).",
                        EXCHANGE_RATE_USD_INR,
                    )
            except Exception as exc:
                logger.error("Failed to convert product prices during currency change: %s", exc)

        try:
            execute_update_or_delete(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES ('currency', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
                """,
                (code,),
                custom_path=custom_path,
            )
            logger.info("Persisted currency preference '%s' in database.", code)
        except Exception as exc:
            logger.error("Failed to persist currency preference: %s", exc)
        return code

    @staticmethod
    def get_currency_symbol(custom_path: Optional[Union[str, Path]] = None) -> str:
        """Return the active currency symbol ('₹' or '$'). Defaults to '₹'."""
        code = SettingsService.get_currency_preference(custom_path=custom_path)
        return CURRENCY_SYMBOLS.get(code, "₹")

    @staticmethod
    def format_currency(amount: float, custom_path: Optional[Union[str, Path]] = None) -> str:
        """Format a numeric price/amount with the active currency symbol."""
        symbol = SettingsService.get_currency_symbol(custom_path=custom_path)
        return f"{symbol}{amount:,.2f}"

    @staticmethod
    def delete_user_and_reset_database(
        user_id: int,
        password: str,
        custom_path: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Verify user's password and permanently delete user, inventory, and session data.
        
        Raises:
            ValueError: If password is incorrect or user account does not exist.
        """
        if not password or not password.strip():
            raise ValueError("Current password is required to confirm account deletion.")

        sql = "SELECT id, password_hash, salt, username FROM users WHERE id = ?;"
        row = fetch_one(sql, (user_id,), custom_path=custom_path)
        if not row:
            raise ValueError("User account not found.")

        if not verify_password(password, row["password_hash"], row["salt"]):
            logger.warning("Account deletion aborted: incorrect password for user ID %s.", user_id)
            raise ValueError("Incorrect password. Account deletion cancelled.")

        logger.warning(
            "Permanently deleting user '%s' (ID %s) and resetting local database...",
            row["username"],
            user_id,
        )

        with get_db_connection(custom_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products;")
            cursor.execute("DELETE FROM users;")
            cursor.execute("DELETE FROM app_settings;")
            conn.commit()

        # Reclaim space and vacuum
        try:
            with get_db_connection(custom_path) as conn:
                conn.execute("VACUUM;")
        except Exception as exc:
            logger.debug("Vacuum after reset skipped: %s", exc)

        logger.info("Database reset complete. All products, users, and session settings cleared.")
        return True
