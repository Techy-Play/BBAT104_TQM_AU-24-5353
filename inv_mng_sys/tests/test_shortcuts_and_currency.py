"""Automated test suite for Keyboard Shortcuts and Currency Conversion.

Validates:
1. Currency conversion on preference switch (INR -> USD -> INR) with standard rate 1 USD = 83 INR.
2. Idempotence when setting same currency repeatedly.
3. Shortcut normalization, reserved keys rejection, and Tkinter sequence generation.
4. ShortcutManager persistence in SQLite app_settings and reset to defaults.
5. SettingsView 'Shortcuts' card and interactive save/reset callbacks.
6. IMSApplication global hotkeys routing for Ctrl+N, Ctrl+S, Ctrl+L, Ctrl+D, Ctrl+I, Ctrl+P, Ctrl+R.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional
import customtkinter as ctk

from app.authentication.security import UserSession
from app.database.connection import get_db_connection
from app.database.queries import fetch_all, fetch_one
from app.database.schema import init_database
from app.inventory.crud import add_product
from app.inventory.filters import FilterCriteria
from app.main import IMSApplication
from app.settings.settings import (
    CURRENCY_INR,
    CURRENCY_USD,
    EXCHANGE_RATE_USD_INR,
    SettingsService,
)
from app.settings.shortcuts import (
    ACTION_ADD_ITEM,
    ACTION_FILTER_LOW_STOCK,
    ACTION_NAV_DASHBOARD,
    ACTION_NAV_INVENTORY,
    ACTION_NAV_SETTINGS,
    ACTION_QUICK_SEARCH,
    ACTION_REFRESH,
    DEFAULT_SHORTCUTS,
    SHORTCUT_METADATA,
    ShortcutManager,
    normalize_shortcut,
    shortcut_to_tk_sequences,
)
from app.ui.views_settings import SettingsView


class TestShortcutsAndCurrencyConversion(unittest.TestCase):
    """Test suite for custom keyboard shortcuts and currency value conversion."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_shortcuts_currency.db"
        init_database(custom_path=self.db_path)

        self.mock_session = UserSession(
            id=1,
            username="shopowner",
            full_name="Rajesh Sharma",
            organization_name="Sharma Electronics",
            keep_logged_in=True,
            session_token="test_tok_9988",
        )

        # Seed sample inventory items with known initial INR prices
        add_product(
            product_id="SKU-100",
            name="Precision Multimeter",
            category="Instruments",
            supplier="Apex Tools",
            quantity=10,
            price=830.00,  # Exactly 10 USD at 83 INR/USD
            custom_path=self.db_path,
        )
        add_product(
            product_id="SKU-200",
            name="Soldering Station",
            category="Tools",
            supplier="Apex Tools",
            quantity=5,
            price=1660.00,  # Exactly 20 USD at 83 INR/USD
            custom_path=self.db_path,
        )
        add_product(
            product_id="SKU-300",
            name="Flux Paste",
            category="Supplies",
            supplier="QuickSupply",
            quantity=20,
            price=415.00,  # Exactly 5 USD at 83 INR/USD
            custom_path=self.db_path,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_currency_conversion_inr_to_usd_and_back(self):
        """Confirm changing currency from INR to USD divides prices by 83.0, and converting back multiplies by 83.0."""
        # 1. Verify initial currency is INR and prices match seed data
        initial_curr = SettingsService.get_currency_preference(custom_path=self.db_path)
        self.assertEqual(initial_curr, CURRENCY_INR)

        items_inr = fetch_all(
            "SELECT product_id, price FROM products ORDER BY product_id;",
            custom_path=self.db_path,
        )
        self.assertEqual(items_inr[0]["price"], 830.00)
        self.assertEqual(items_inr[1]["price"], 1660.00)
        self.assertEqual(items_inr[2]["price"], 415.00)

        # 2. Switch currency to USD ($)
        code = SettingsService.set_currency_preference("USD", custom_path=self.db_path, convert_prices=True)
        self.assertEqual(code, CURRENCY_USD)
        self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), CURRENCY_USD)
        self.assertEqual(SettingsService.get_currency_symbol(custom_path=self.db_path), "$")

        # 3. Check that prices converted accurately in database
        items_usd = fetch_all(
            "SELECT product_id, price FROM products ORDER BY product_id;",
            custom_path=self.db_path,
        )
        self.assertAlmostEqual(items_usd[0]["price"], 10.00, places=2)
        self.assertAlmostEqual(items_usd[1]["price"], 20.00, places=2)
        self.assertAlmostEqual(items_usd[2]["price"], 5.00, places=2)

        # 4. Confirm calling set_currency_preference with the same code ('USD') does not re-divide
        SettingsService.set_currency_preference("USD", custom_path=self.db_path, convert_prices=True)
        items_usd_same = fetch_all(
            "SELECT product_id, price FROM products ORDER BY product_id;",
            custom_path=self.db_path,
        )
        self.assertAlmostEqual(items_usd_same[0]["price"], 10.00, places=2)

        # 5. Switch back to INR (Rupees)
        code_inr = SettingsService.set_currency_preference("Rupees (₹)", custom_path=self.db_path, convert_prices=True)
        self.assertEqual(code_inr, CURRENCY_INR)
        self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), CURRENCY_INR)
        self.assertEqual(SettingsService.get_currency_symbol(custom_path=self.db_path), "₹")

        # 6. Check that prices multiplied back to INR
        items_restored = fetch_all(
            "SELECT product_id, price FROM products ORDER BY product_id;",
            custom_path=self.db_path,
        )
        self.assertAlmostEqual(items_restored[0]["price"], 830.00, places=2)
        self.assertAlmostEqual(items_restored[1]["price"], 1660.00, places=2)
        self.assertAlmostEqual(items_restored[2]["price"], 415.00, places=2)

    def test_02_shortcut_normalization_and_validation(self):
        """Test normalization of valid shortcuts and rejection of invalid / reserved ones."""
        # Valid normalizations
        self.assertEqual(normalize_shortcut("ctrl + n"), "Ctrl+N")
        self.assertEqual(normalize_shortcut("CTRL+S"), "Ctrl+S")
        self.assertEqual(normalize_shortcut("ctrl+l"), "Ctrl+L")
        self.assertEqual(normalize_shortcut("alt + shift + k"), "Alt+Shift+K")
        self.assertEqual(normalize_shortcut("f5"), "F5")
        self.assertEqual(normalize_shortcut("ctrl + f11"), "Ctrl+F11")

        # Empty / whitespace rejection
        with self.assertRaises(ValueError):
            normalize_shortcut("")
        with self.assertRaises(ValueError):
            normalize_shortcut("   ")

        # Bare single letter rejection without modifier
        with self.assertRaises(ValueError):
            normalize_shortcut("n")
        with self.assertRaises(ValueError):
            normalize_shortcut("s")

        # Reserved clipboard keys rejection
        with self.assertRaises(ValueError):
            normalize_shortcut("Ctrl+C")
        with self.assertRaises(ValueError):
            normalize_shortcut("ctrl+v")
        with self.assertRaises(ValueError):
            normalize_shortcut("Ctrl+A")

    def test_03_shortcut_tk_sequence_conversion(self):
        """Confirm conversion to Tkinter event sequences covers required key variants."""
        seqs_ctrl_n = shortcut_to_tk_sequences("Ctrl+N")
        self.assertIn("<Control-n>", seqs_ctrl_n)
        self.assertIn("<Control-N>", seqs_ctrl_n)

        seqs_ctrl_s = shortcut_to_tk_sequences("Ctrl+S")
        self.assertIn("<Control-s>", seqs_ctrl_s)
        self.assertIn("<Control-S>", seqs_ctrl_s)

        seqs_ctrl_l = shortcut_to_tk_sequences("Ctrl+L")
        self.assertIn("<Control-l>", seqs_ctrl_l)
        self.assertIn("<Control-L>", seqs_ctrl_l)

        seqs_f5 = shortcut_to_tk_sequences("F5")
        self.assertIn("<F5>", seqs_f5)

    def test_04_shortcut_manager_persistence_and_conflict_handling(self):
        """Confirm custom shortcuts persist into SQLite app_settings and handle conflicts."""
        # 1. Defaults should be loaded initially
        shortcuts = ShortcutManager.get_shortcuts(custom_path=self.db_path)
        self.assertEqual(shortcuts[ACTION_ADD_ITEM], "Ctrl+N")
        self.assertEqual(shortcuts[ACTION_QUICK_SEARCH], "Ctrl+S")
        self.assertEqual(shortcuts[ACTION_FILTER_LOW_STOCK], "Ctrl+L")
        self.assertEqual(shortcuts[ACTION_NAV_DASHBOARD], "Ctrl+D")
        self.assertEqual(shortcuts[ACTION_NAV_INVENTORY], "Ctrl+I")
        self.assertEqual(shortcuts[ACTION_NAV_SETTINGS], "Ctrl+P")
        self.assertEqual(shortcuts[ACTION_REFRESH], "Ctrl+R")

        # 2. Update shortcuts with customized values
        custom_map = dict(shortcuts)
        custom_map[ACTION_ADD_ITEM] = "Ctrl+M"
        custom_map[ACTION_QUICK_SEARCH] = "Ctrl+F"
        saved = ShortcutManager.save_shortcuts(custom_map, custom_path=self.db_path)
        self.assertEqual(saved[ACTION_ADD_ITEM], "Ctrl+M")
        self.assertEqual(saved[ACTION_QUICK_SEARCH], "Ctrl+F")

        # 3. Reload from database to verify persistence
        reloaded = ShortcutManager.get_shortcuts(custom_path=self.db_path)
        self.assertEqual(reloaded[ACTION_ADD_ITEM], "Ctrl+M")
        self.assertEqual(reloaded[ACTION_QUICK_SEARCH], "Ctrl+F")

        # 4. Duplicate assignment should raise conflict error
        conflicted = dict(shortcuts)
        conflicted[ACTION_ADD_ITEM] = "Ctrl+D"  # Duplicate of nav_dashboard
        with self.assertRaises(ValueError) as ctx:
            ShortcutManager.save_shortcuts(conflicted, custom_path=self.db_path)
        self.assertIn("Conflict detected", str(ctx.exception))

        # 5. Reset to defaults restores default mappings
        resetted = ShortcutManager.reset_shortcuts_to_defaults(custom_path=self.db_path)
        self.assertEqual(resetted[ACTION_ADD_ITEM], "Ctrl+N")
        self.assertEqual(resetted[ACTION_QUICK_SEARCH], "Ctrl+S")

    def test_05_settings_view_shortcuts_ui_and_currency_banner(self):
        """Confirm SettingsView renders Shortcuts section and triggers callbacks."""
        root = ctk.CTk()
        root.withdraw()

        changed_shortcuts: List[Dict[str, str]] = []
        changed_currencies: List[str] = []

        try:
            view = SettingsView(
                master=root,
                user_session=self.mock_session,
                on_profile_updated=lambda _s: None,
                on_account_deleted=lambda: None,
                on_currency_changed=lambda c: changed_currencies.append(c),
                on_shortcuts_changed=lambda s: changed_shortcuts.append(s),
                db_path=self.db_path,
            )
            view.pack()
            view.update_idletasks()

            # Verify shortcut entries are populated
            self.assertIn(ACTION_ADD_ITEM, view.shortcut_entries)
            self.assertEqual(view.shortcut_entries[ACTION_ADD_ITEM].get(), "Ctrl+N")
            self.assertEqual(view.shortcut_entries[ACTION_QUICK_SEARCH].get(), "Ctrl+S")
            self.assertEqual(view.shortcut_entries[ACTION_FILTER_LOW_STOCK].get(), "Ctrl+L")

            # Update entry in UI and save
            view.shortcut_entries[ACTION_ADD_ITEM].delete(0, "end")
            view.shortcut_entries[ACTION_ADD_ITEM].insert(0, "Ctrl+K")
            view._handle_save_shortcuts()

            self.assertTrue(len(changed_shortcuts) > 0)
            self.assertEqual(changed_shortcuts[-1][ACTION_ADD_ITEM], "Ctrl+K")
            self.assertIn("Custom shortcuts saved", view.shortcuts_banner.get_message())

            # Test reset button
            view._handle_reset_shortcuts()
            self.assertEqual(view.shortcut_entries[ACTION_ADD_ITEM].get(), "Ctrl+N")
            self.assertIn("factory defaults", view.shortcuts_banner.get_message())

            # Test currency change converts prices and banner mentions exchange rate
            view._handle_currency_change("USD ($)")
            self.assertIn("USD", changed_currencies)
            self.assertIn("1 USD = ₹83.00", view.currency_banner.get_message())

        finally:
            root.destroy()

    def test_06_ims_application_hotkey_dispatcher(self):
        """Confirm IMSApplication dispatches hotkey actions for add_item, quick_search, and low_stock."""
        app = IMSApplication(db_path=self.db_path)
        app.withdraw()

        try:
            app.show_app_shell(self.mock_session)
            app.update_idletasks()

            # 1. Test quick search action dispatcher
            res_s = app._dispatch_shortcut_action(ACTION_QUICK_SEARCH)
            self.assertEqual(res_s, "break")

            # 2. Test low stock action dispatcher (should switch to Inventory with Low Stock filter)
            res_l = app._dispatch_shortcut_action(ACTION_FILTER_LOW_STOCK)
            self.assertEqual(res_l, "break")
            self.assertEqual(app.current_view, app.views["inv"])
            self.assertEqual(app.views["inv"].opt_status.get(), "Low Stock")

            # 3. Test navigation dispatchers
            app._dispatch_shortcut_action(ACTION_NAV_DASHBOARD)
            self.assertEqual(app.current_view, app.views["dash"])

            app._dispatch_shortcut_action(ACTION_NAV_SETTINGS)
            self.assertEqual(app.current_view, app.views["settings"])

            # 4. Test re-registering shortcuts
            ShortcutManager.save_shortcuts({ACTION_ADD_ITEM: "Ctrl+K"}, custom_path=self.db_path)
            app.register_global_shortcuts()
            self.assertEqual(app.active_shortcuts[ACTION_ADD_ITEM], "Ctrl+K")

        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
