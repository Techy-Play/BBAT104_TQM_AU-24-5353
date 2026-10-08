"""Automated tests for Phase 3 (First-Run Setup) and Phase 4 (Authentication & Security).

Validates:
1. First user creation.
2. Username uniqueness.
3. Password hashing.
4. Correct password verification.
5. Incorrect password rejection.
6. Plaintext password exclusion.
7. Session token generation.
8. Keep Me Logged In behavior.
9. Session restoration.
10. Session invalidation on logout.
11. User profile retrieval and update.
12. Persistence across database closing and reopening.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
import sqlite3

from app.authentication.login import (
    authenticate_user,
    change_user_password,
    get_user_profile,
    logout_user,
    restore_session,
    update_keep_logged_in_preference,
    update_user_profile,
)
from app.authentication.security import (
    generate_salt,
    generate_session_token,
    hash_password,
    verify_password,
)
from app.authentication.setup import is_first_run, register_first_user, validate_setup_data
from app.database.queries import fetch_one, get_setting
from app.database.schema import init_database


class TestAuthenticationAndSecurity(unittest.TestCase):
    """Test suite for authentication, security hashing, session management, and profile."""

    def setUp(self) -> None:
        """Create a temporary isolated SQLite database for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_auth.db"
        init_database(self.db_path)

    def tearDown(self) -> None:
        """Remove temporary directory after test execution."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_first_user_creation(self) -> None:
        """Confirm first-run detection and initial user creation."""
        self.assertTrue(is_first_run(self.db_path))

        session = register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="lokesh",
            password="secretPassword123",
            confirm_password="secretPassword123",
            keep_logged_in=False,
            custom_path=self.db_path,
        )

        self.assertIsNotNone(session)
        self.assertEqual(session.username, "lokesh")
        self.assertEqual(session.full_name, "Lokesh Paneru")
        self.assertEqual(session.organization_name, "Apex Electronics")
        self.assertFalse(session.keep_logged_in)
        self.assertFalse(is_first_run(self.db_path))

    def test_02_username_uniqueness(self) -> None:
        """Confirm duplicate username registration is rejected."""
        register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="unique_user",
            password="password123",
            confirm_password="password123",
            custom_path=self.db_path,
        )

        # Attempting identical username (even with different case) must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            register_first_user(
                full_name="Another User",
                org_name="Other Org",
                username="UNIQUE_USER",
                password="differentPassword123",
                confirm_password="differentPassword123",
                custom_path=self.db_path,
            )
        self.assertIn("already taken", str(ctx.exception).lower())

    def test_03_password_hashing(self) -> None:
        """Confirm PBKDF2 password hashing produces distinct hashes with different salts."""
        pwd = "SecurePassword@2026"
        salt1 = generate_salt()
        salt2 = generate_salt()

        hash1 = hash_password(pwd, salt1)
        hash2 = hash_password(pwd, salt2)

        self.assertEqual(len(hash1), 64)  # 256-bit hash in hex
        self.assertEqual(len(hash2), 64)
        self.assertNotEqual(hash1, hash2)  # Different salts produce different hashes

    def test_04_correct_password_verification(self) -> None:
        """Confirm correct password verifies and authenticates."""
        salt = generate_salt()
        pwd = "MySecretPassword123"
        hashed = hash_password(pwd, salt)
        self.assertTrue(verify_password(pwd, hashed, salt))

        register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="lokesh",
            password=pwd,
            confirm_password=pwd,
            custom_path=self.db_path,
        )

        session = authenticate_user("lokesh", pwd, custom_path=self.db_path)
        self.assertIsNotNone(session)
        self.assertEqual(session.username, "lokesh")

    def test_05_incorrect_password_rejection(self) -> None:
        """Confirm incorrect password or nonexistent user is rejected with generic error."""
        pwd = "CorrectPassword123"
        register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="lokesh",
            password=pwd,
            confirm_password=pwd,
            custom_path=self.db_path,
        )

        # Wrong password
        with self.assertRaises(ValueError) as ctx:
            authenticate_user("lokesh", "WrongPassword999", custom_path=self.db_path)
        self.assertEqual(str(ctx.exception), "Invalid username or password.")

        # Nonexistent user
        with self.assertRaises(ValueError) as ctx:
            authenticate_user("unknown_user", pwd, custom_path=self.db_path)
        self.assertEqual(str(ctx.exception), "Invalid username or password.")

    def test_06_password_not_stored_as_plaintext(self) -> None:
        """Verify the database strictly stores salted hashes, never plaintext passwords."""
        plain_pwd = "SuperSecretPlaintextPassword!"
        register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="security_tester",
            password=plain_pwd,
            confirm_password=plain_pwd,
            custom_path=self.db_path,
        )

        row = fetch_one(
            "SELECT password_hash, salt FROM users WHERE username = 'security_tester';",
            custom_path=self.db_path,
        )
        self.assertIsNotNone(row)
        self.assertNotEqual(row["password_hash"], plain_pwd)
        self.assertNotIn(plain_pwd, row["password_hash"])
        self.assertNotIn(plain_pwd, row["salt"])

    def test_07_session_token_generation(self) -> None:
        """Confirm session token generation produces 64-character unique cryptographic strings."""
        token1 = generate_session_token()
        token2 = generate_session_token()

        self.assertEqual(len(token1), 64)
        self.assertEqual(len(token2), 64)
        self.assertNotEqual(token1, token2)

    def test_08_keep_me_logged_in_behavior(self) -> None:
        """Verify Keep Me Logged In sets session tokens and preferences correctly."""
        pwd = "ValidPassword123"
        register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="lokesh",
            password=pwd,
            confirm_password=pwd,
            keep_logged_in=False,
            custom_path=self.db_path,
        )

        # Login without keep_logged_in
        session_no_keep = authenticate_user("lokesh", pwd, keep_logged_in=False, custom_path=self.db_path)
        self.assertFalse(session_no_keep.keep_logged_in)
        self.assertIsNone(session_no_keep.session_token)

        active_setting = get_setting("active_session_token", custom_path=self.db_path)
        self.assertEqual(active_setting, "")

        # Login WITH keep_logged_in
        session_keep = authenticate_user("lokesh", pwd, keep_logged_in=True, custom_path=self.db_path)
        self.assertTrue(session_keep.keep_logged_in)
        self.assertIsNotNone(session_keep.session_token)
        self.assertEqual(len(session_keep.session_token), 64)

        active_setting_after = get_setting("active_session_token", custom_path=self.db_path)
        self.assertEqual(active_setting_after, session_keep.session_token)

    def test_09_session_restoration(self) -> None:
        """Confirm valid Keep Me Logged In session is restored automatically."""
        pwd = "ValidPassword123"
        register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="lokesh",
            password=pwd,
            confirm_password=pwd,
            keep_logged_in=True,
            custom_path=self.db_path,
        )

        # Restore session
        restored = restore_session(custom_path=self.db_path)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.username, "lokesh")
        self.assertEqual(restored.full_name, "Lokesh Paneru")
        self.assertTrue(restored.keep_logged_in)

    def test_10_session_invalidation_logout(self) -> None:
        """Confirm logout invalidates session token and prevents restoration."""
        pwd = "ValidPassword123"
        session = register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="lokesh",
            password=pwd,
            confirm_password=pwd,
            keep_logged_in=True,
            custom_path=self.db_path,
        )

        # Log out
        logout_user(session.id, custom_path=self.db_path)

        # Verify restoration returns None
        restored = restore_session(custom_path=self.db_path)
        self.assertIsNone(restored)

        # Verify database record
        row = fetch_one("SELECT session_token, keep_logged_in FROM users WHERE id = ?;", (session.id,), custom_path=self.db_path)
        self.assertIsNone(row["session_token"])
        self.assertEqual(row["keep_logged_in"], 0)

        # Verify app_settings token is cleared
        setting_val = get_setting("active_session_token", custom_path=self.db_path)
        self.assertEqual(setting_val, "")

    def test_11_user_profile_retrieval_and_update(self) -> None:
        """Confirm profile retrieval, editing, and password change."""
        pwd = "InitialPassword123"
        session = register_first_user(
            full_name="Initial Name",
            org_name="Initial Org",
            username="profile_user",
            password=pwd,
            confirm_password=pwd,
            custom_path=self.db_path,
        )

        # Retrieve profile
        profile = get_user_profile(session.id, custom_path=self.db_path)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.full_name, "Initial Name")

        # Update profile
        updated = update_user_profile(session.id, "Updated Name", "Updated Business", custom_path=self.db_path)
        self.assertEqual(updated.full_name, "Updated Name")
        self.assertEqual(updated.organization_name, "Updated Business")

        # Change password
        new_pwd = "UpdatedPassword456"
        change_user_password(session.id, pwd, new_pwd, new_pwd, custom_path=self.db_path)

        # Authenticate with new password
        new_session = authenticate_user("profile_user", new_pwd, custom_path=self.db_path)
        self.assertIsNotNone(new_session)

        # Old password must now fail
        with self.assertRaises(ValueError):
            authenticate_user("profile_user", pwd, custom_path=self.db_path)

    def test_12_persistence_after_database_close_reopen(self) -> None:
        """Confirm session and user persistence across database reopen and restart."""
        pwd = "PersistentPassword123"
        session = register_first_user(
            full_name="Lokesh Paneru",
            org_name="Apex Electronics",
            username="lokesh",
            password=pwd,
            confirm_password=pwd,
            keep_logged_in=True,
            custom_path=self.db_path,
        )

        # Simulate full application restart by re-initializing database schema
        restart_status = init_database(self.db_path)
        self.assertTrue(restart_status["existed_before"])

        # Restoring session must still succeed
        restored = restore_session(custom_path=self.db_path)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.username, "lokesh")
        self.assertEqual(restored.full_name, "Lokesh Paneru")
        self.assertEqual(restored.organization_name, "Apex Electronics")


if __name__ == "__main__":
    unittest.main()
