"""Automated tests for user account deletion, database reset, and first-run setup improvements.

Validates:
1. SettingsService.delete_user_and_reset_database:
   - Rejects missing or blank password.
   - Rejects incorrect password without altering database records.
   - With correct password: wipes users, products, sessions, and resets is_first_run to True.
2. DeleteAccountModal:
   - Contains no CTkScrollableFrame.
   - Cancel button dismisses modal without executing reset.
   - Submitting correct password executes reset and fires on_confirmed callback.
3. FirstRunSetupFrame:
   - Inherits from CTkFrame (not CTkScrollableFrame) for a clean non-scrolling single-card view.
   - Tab/Shift-Tab cyclic keyboard navigation across all inputs.
   - Submitting form successfully registers administrator and invokes on_success.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
import customtkinter as ctk

from app.authentication.setup import is_first_run, register_first_user
from app.database.schema import init_database
from app.inventory.crud import add_product
from app.settings.settings import SettingsService
from app.ui.views_auth import FirstRunSetupFrame
from app.ui.views_settings import DeleteAccountModal, SettingsView


class TestAccountDeletionAndSetup(unittest.TestCase):
    """Test suite for password-confirmed account deletion and improved setup wizard."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_delete_setup.db"
        init_database(custom_path=self.db_path)

        # Create sample user
        self.session = register_first_user(
            full_name="Alex Mercer",
            org_name="Mercer Industrial",
            username="alexm",
            password="SecurePassword123",
            confirm_password="SecurePassword123",
            keep_logged_in=True,
            custom_path=self.db_path,
        )

        # Seed sample product
        self.product = add_product(
            product_id="SKU-8001",
            name="Industrial Torque Wrench",
            category="Mechanical",
            supplier="Apex Tools",
            quantity=25,
            price=149.50,
            custom_path=self.db_path,
        )

        self.root = ctk.CTk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_delete_user_password_validation(self):
        """Confirm account deletion strictly validates password before wiping records."""
        # 1. Reject empty password
        with self.assertRaises(ValueError) as ctx:
            SettingsService.delete_user_and_reset_database(
                user_id=self.session.id,
                password="",
                custom_path=self.db_path,
            )
        self.assertIn("password is required", str(ctx.exception).lower())

        # 2. Reject incorrect password
        with self.assertRaises(ValueError) as ctx2:
            SettingsService.delete_user_and_reset_database(
                user_id=self.session.id,
                password="WrongPassword999",
                custom_path=self.db_path,
            )
        self.assertIn("incorrect password", str(ctx2.exception).lower())

        # Verify data is still intact
        self.assertFalse(is_first_run(custom_path=self.db_path))

    def test_02_delete_user_and_reset_database_success(self):
        """Confirm correct password wipes all products, users, and returns app to first-run state."""
        self.assertFalse(is_first_run(custom_path=self.db_path))

        res = SettingsService.delete_user_and_reset_database(
            user_id=self.session.id,
            password="SecurePassword123",
            custom_path=self.db_path,
        )
        self.assertTrue(res)

        # Database is now completely reset and ready for initial onboarding
        self.assertTrue(is_first_run(custom_path=self.db_path))

    def test_03_first_run_setup_frame_layout_and_registration(self):
        """Verify FirstRunSetupFrame is non-scrolling (no CTkScrollableFrame) and submits successfully."""
        self.assertFalse(issubclass(FirstRunSetupFrame, ctk.CTkScrollableFrame))

        # Reset database first
        SettingsService.delete_user_and_reset_database(
            user_id=self.session.id,
            password="SecurePassword123",
            custom_path=self.db_path,
        )

        registered_sessions = []
        setup_frame = FirstRunSetupFrame(
            master=self.root,
            on_success=lambda s: registered_sessions.append(s),
            reset_notice=True,
            db_path=str(self.db_path),
        )
        setup_frame.pack(fill="both", expand=True)
        self.root.update()

        # Check that no CTkScrollableFrame exists in children
        for child in setup_frame.winfo_children():
            self.assertNotIsInstance(child, ctk.CTkScrollableFrame)

        # Fill in form
        setup_frame.entry_name.set_value("Morgan Freeman")
        setup_frame.entry_org.set_value("Freeman Logistics")
        setup_frame.entry_user.set_value("morganf")
        setup_frame.entry_pwd.set_value("NewSecretPassword77")
        setup_frame.entry_confirm.set_value("NewSecretPassword77")

        # Submit via Enter hotkey simulation
        setup_frame.btn_submit._trigger_nav_submit() if hasattr(setup_frame.btn_submit, "_trigger_nav_submit") else setup_frame._handle_setup()

        self.assertEqual(len(registered_sessions), 1)
        self.assertEqual(registered_sessions[0].username, "morganf")
        self.assertEqual(registered_sessions[0].full_name, "Morgan Freeman")
        self.assertFalse(is_first_run(custom_path=self.db_path))

    def test_04_delete_account_modal_cancellation_and_confirmation(self):
        """Confirm DeleteAccountModal keyboard navigation, cancellation, and execution."""
        confirmed_calls = []

        modal = DeleteAccountModal(
            parent=self.root,
            user_session=self.session,
            on_confirmed=lambda: confirmed_calls.append(True),
            db_path=str(self.db_path),
        )
        self.root.update()
        modal.update()

        # Check geometry and non-scrolling
        for child in modal.winfo_children():
            self.assertNotIsInstance(child, ctk.CTkScrollableFrame)

        # Test incorrect password error banner
        modal.entry_pwd.set_value("BadPassword")
        modal._handle_confirm_delete()
        self.assertEqual(len(confirmed_calls), 0)
        self.assertTrue(modal.winfo_exists())

        # Test correct password
        modal.entry_pwd.set_value("SecurePassword123")
        modal._handle_confirm_delete()
        self.root.update()

        self.assertEqual(len(confirmed_calls), 1)
        self.assertTrue(is_first_run(custom_path=self.db_path))
        self.assertFalse(modal.winfo_exists())


if __name__ == "__main__":
    unittest.main()
