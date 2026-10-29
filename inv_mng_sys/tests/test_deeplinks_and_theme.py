"""Automated test suite for Dashboard Deep Links, Login UI, and Theme Persistence.

Covers:
1. Theme persistence in SQLite settings table (default 'system', updating to 'dark', 'light').
2. Theme display string format and parse helpers.
3. SettingsService theme preference retrieval across simulated application restart.
4. DashboardFrame deep linking callback invocation for StatCards:
   - Total Products (None / All)
   - Total Stock Qty (Quantity DESC)
   - Low Stock Alerts (stock_status='Low Stock')
   - Out of Stock (stock_status='Out of Stock')
5. DashboardFrame Quick-Search deep link ("Open in Inventory ↗").
6. DashboardFrame row-level deep link ("Open ↗").
7. InventoryView initial_criteria handling and filter pre-population.
8. IMSApplication dynamic window resizing logic for Login vs Shell vs Logout.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Optional

from app.authentication.security import UserSession
from app.dashboard.dashboard import DashboardFrame
from app.database.schema import init_database
from app.inventory.crud import add_product
from app.inventory.filters import FilterCriteria
from app.main import IMSApplication
from app.settings.settings import SettingsService
from app.ui.theme import (
    THEME_MODES,
    get_theme_display_string,
    parse_theme_mode,
)
from app.ui.views_inventory import InventoryView
from app.ui.views_settings import SettingsView


class TestDeepLinksAndThemePersistence(unittest.TestCase):
    """Test suite verifying deep links, theme persistence, and window geometry."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_ims.db"
        init_database(custom_path=self.db_path)

        self.mock_session = UserSession(
            id=1,
            username="admin",
            full_name="Test Administrator",
            organization_name="Test Warehouse Corp",
            keep_logged_in=True,
            session_token="test_token_12345",
        )

        # Seed sample products
        add_product(
            product_id="SKU-101",
            name="Industrial Drill Press",
            category="Machinery",
            supplier="ToolMaster Inc",
            quantity=25,
            price=499.99,
            custom_path=self.db_path,
        )
        add_product(
            product_id="SKU-102",
            name="Safety Goggles",
            category="Safety",
            supplier="SafeGuard Supplies",
            quantity=5,  # Low stock
            price=15.50,
            custom_path=self.db_path,
        )
        add_product(
            product_id="SKU-103",
            name="Heavy Duty Gloves",
            category="Safety",
            supplier="SafeGuard Supplies",
            quantity=0,  # Out of stock
            price=12.00,
            custom_path=self.db_path,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_default_theme_is_device_default_system(self):
        """Confirm default theme is 'system' (device default) when unconfigured."""
        theme = SettingsService.get_theme_preference(custom_path=self.db_path)
        self.assertEqual(theme, "system")

    def test_02_theme_persistence_and_reopen(self):
        """Confirm theme selection persists across saves and database reopen."""
        # Save dark mode
        SettingsService.set_theme_preference("dark", custom_path=self.db_path)
        self.assertEqual(SettingsService.get_theme_preference(custom_path=self.db_path), "dark")

        # Save light mode
        SettingsService.set_theme_preference("light", custom_path=self.db_path)
        self.assertEqual(SettingsService.get_theme_preference(custom_path=self.db_path), "light")

        # Reopen simulated: new query on existing path
        saved = SettingsService.get_theme_preference(custom_path=self.db_path)
        self.assertEqual(saved, "light")

    def test_03_theme_helpers_and_symbols(self):
        """Verify theme display labels include appropriate theme-aware symbols."""
        sys_str = get_theme_display_string("system")
        dark_str = get_theme_display_string("dark")
        light_str = get_theme_display_string("light")

        self.assertIn("💻", sys_str)
        self.assertIn("System", sys_str)

        self.assertIn("🌙", dark_str)
        self.assertIn("Dark", dark_str)

        self.assertIn("☀️", light_str)
        self.assertIn("Light", light_str)

        self.assertEqual(parse_theme_mode(sys_str), "system")
        self.assertEqual(parse_theme_mode(dark_str), "dark")
        self.assertEqual(parse_theme_mode(light_str), "light")
        self.assertEqual(parse_theme_mode("unknown fallback"), "system")

    def test_04_dashboard_statcard_deep_links(self):
        """Verify StatCard deep link clicks route to Inventory with exact FilterCriteria."""
        dispatched_criteria: list[Optional[FilterCriteria]] = []

        def mock_navigate(criteria: Optional[FilterCriteria] = None):
            dispatched_criteria.append(criteria)

        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()

        try:
            dash = DashboardFrame(
                master=root,
                user_session=self.mock_session,
                on_navigate_inventory=mock_navigate,
                on_navigate_settings=lambda: None,
                on_logout=lambda: None,
                db_path=str(self.db_path),
            )

            # Test Total Products deep link
            dash.card_total.on_click_callback()
            self.assertEqual(len(dispatched_criteria), 1)
            self.assertIsNone(dispatched_criteria[-1])

            # Test Total Qty deep link (sorted by quantity DESC)
            dash.card_qty.on_click_callback()
            self.assertEqual(len(dispatched_criteria), 2)
            qty_crit = dispatched_criteria[-1]
            self.assertIsNotNone(qty_crit)
            self.assertEqual(qty_crit.sort_by, "Quantity")
            self.assertEqual(qty_crit.sort_direction, "DESC")

            # Test Low Stock deep link
            dash.card_low.on_click_callback()
            self.assertEqual(len(dispatched_criteria), 3)
            low_crit = dispatched_criteria[-1]
            self.assertIsNotNone(low_crit)
            self.assertEqual(low_crit.stock_status, "Low Stock")

            # Test Out of Stock deep link
            dash.card_out.on_click_callback()
            self.assertEqual(len(dispatched_criteria), 4)
            out_crit = dispatched_criteria[-1]
            self.assertIsNotNone(out_crit)
            self.assertEqual(out_crit.stock_status, "Out of Stock")

            # Test Total Valuation deep link (sorted by price DESC)
            dash.card_val.on_click_callback()
            self.assertEqual(len(dispatched_criteria), 5)
            val_crit = dispatched_criteria[-1]
            self.assertIsNotNone(val_crit)
            self.assertEqual(val_crit.sort_by, "Price")
            self.assertEqual(val_crit.sort_direction, "DESC")

            # Test Category Analysis row deep link
            self.assertGreater(len(dash._category_row_pool), 0)
            dash._category_row_pool[0]._handle_click()
            self.assertEqual(len(dispatched_criteria), 6)
            cat_crit = dispatched_criteria[-1]
            self.assertIsNotNone(cat_crit)
            self.assertTrue(bool(cat_crit.category))

            # Test Quick Search 'Open in Inventory' deep link
            dash.quick_search_entry.insert(0, "Drill")
            dash._handle_open_in_inventory()
            self.assertEqual(len(dispatched_criteria), 7)
            q_crit = dispatched_criteria[-1]
            self.assertIsNotNone(q_crit)
            self.assertEqual(q_crit.search_query, "Drill")
        finally:
            root.destroy()

    def test_05_inventory_view_accepts_initial_criteria(self):
        """Verify InventoryView applies initial_criteria on instantiation."""
        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()

        try:
            crit = FilterCriteria(
                search_query="Goggles",
                stock_status="Low Stock",
                sort_by="Price",
                sort_direction="ASC",
            )
            inv_view = InventoryView(
                master=root,
                db_path=str(self.db_path),
                initial_criteria=crit,
            )

            # Check pre-filled inputs
            self.assertEqual(inv_view.search_entry.get(), "Goggles")
            self.assertEqual(inv_view.opt_status.get(), "Low Stock")
            self.assertEqual(inv_view.opt_sort_col.get(), "Price")
            self.assertEqual(inv_view.opt_sort_dir.get(), "Ascending")

            # Check filtered product list matches
            self.assertEqual(len(inv_view.products), 1)
            self.assertEqual(inv_view.products[0].product_id, "SKU-102")
        finally:
            root.destroy()

    def test_06_app_window_geometry_logic(self):
        """Verify IMSApplication _resize_and_center calculates appropriate geometries."""
        app = IMSApplication(db_path=str(self.db_path))

        try:
            # Login window size
            app.show_login()
            app.update()
            self.assertEqual((app.target_width, app.target_height), (480, 600))
            geo = app.geometry()
            self.assertTrue(geo.startswith("480x600"), f"Expected 480x600 but got {geo}")

            # Workspace shell window size
            app.show_app_shell(self.mock_session)
            app.update()
            self.assertEqual((app.target_width, app.target_height), (1100, 750))
            geo = app.geometry()
            self.assertTrue(geo.startswith("1100x750"), f"Expected 1100x750 but got {geo}")

            # Sizing upon logout contracts back to login
            app.handle_logout()
            app.update()
            self.assertEqual((app.target_width, app.target_height), (480, 600))
            geo = app.geometry()
            self.assertTrue(geo.startswith("480x600"), f"Expected 480x600 but got {geo}")
        finally:
            app.destroy()

    def test_07_currency_preference_defaults_to_rupees(self):
        """Confirm currency preference defaults to Rupees ('INR' / '₹') when unconfigured."""
        currency = SettingsService.get_currency_preference(custom_path=self.db_path)
        self.assertEqual(currency, "INR")

        symbol = SettingsService.get_currency_symbol(custom_path=self.db_path)
        self.assertEqual(symbol, "₹")

        formatted = SettingsService.format_currency(1234.5, custom_path=self.db_path)
        self.assertEqual(formatted, "₹1,234.50")

    def test_08_currency_preference_persistence_and_usd(self):
        """Confirm currency selection persists across changes (Rupees vs USD) and formats accurately."""
        # 1. Switch to USD
        SettingsService.set_currency_preference("USD", custom_path=self.db_path)
        self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), "USD")
        self.assertEqual(SettingsService.get_currency_symbol(custom_path=self.db_path), "$")
        self.assertEqual(SettingsService.format_currency(59.99, custom_path=self.db_path), "$59.99")

        # 2. Switch using display string 'USD ($)'
        SettingsService.set_currency_preference("USD ($)", custom_path=self.db_path)
        self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), "USD")

        # 3. Switch back to Rupees using display string 'Rupees (₹)'
        SettingsService.set_currency_preference("Rupees (₹)", custom_path=self.db_path)
        self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), "INR")
        self.assertEqual(SettingsService.get_currency_symbol(custom_path=self.db_path), "₹")
        self.assertEqual(SettingsService.format_currency(59.99, custom_path=self.db_path), "₹59.99")

        # 4. Graceful fallback on unknown value
        SettingsService.set_currency_preference("INVALID_CODE", custom_path=self.db_path)
        self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), "INR")

    def test_09_settings_view_currency_selector(self):
        """Confirm SettingsView provides exactly 2 currency options, defaults to Rupees, and updates dynamically."""
        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()

        changed_currencies: list[str] = []

        try:
            view = SettingsView(
                master=root,
                user_session=self.mock_session,
                on_profile_updated=lambda _s: None,
                on_account_deleted=lambda: None,
                on_currency_changed=lambda c: changed_currencies.append(c),
                db_path=str(self.db_path),
            )
            root.update()

            # Verify only 2 options exist
            self.assertEqual(view.opt_currency._values, ["Rupees (₹)", "USD ($)"])

            # Verify initial selection is Rupees
            self.assertEqual(view.opt_currency.get(), "Rupees (₹)")

            # Select USD ($)
            view._handle_currency_change("USD ($)")
            self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), "USD")
            self.assertEqual(len(changed_currencies), 1)
            self.assertEqual(changed_currencies[-1], "USD")

            # Select Rupees (₹)
            view._handle_currency_change("Rupees (₹)")
            self.assertEqual(SettingsService.get_currency_preference(custom_path=self.db_path), "INR")
            self.assertEqual(len(changed_currencies), 2)
            self.assertEqual(changed_currencies[-1], "INR")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
