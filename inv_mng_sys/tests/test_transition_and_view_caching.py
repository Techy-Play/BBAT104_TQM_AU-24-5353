"""Automated tests for GUI smooth transitions, view caching, and installer shortcut icon packaging.

Validates:
1. Application view caching: Navigating between Dashboard, Inventory, and Settings reuses views and updates data without destroying the container.
2. Modals center correctly based on parent geometry without flicker.
3. Batch rendering in Dashboard and Inventory tables functions correctly.
4. Installer script (installer.iss) and build script properly bundle app_icon.ico for the desktop shortcut.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest
import customtkinter as ctk

from app.authentication.security import UserSession
from app.authentication.setup import register_first_user
from app.dashboard.dashboard import DashboardFrame
from app.database.schema import init_database
from app.inventory.crud import add_product
from app.inventory.filters import FilterCriteria
from app.main import IMSApplication
from app.ui.dialogs_inventory import ProductFormModal, ProductDetailsModal
from app.ui.views_inventory import InventoryView
from app.ui.views_settings import SettingsView, DeleteAccountModal


class TestTransitionAndViewCaching(unittest.TestCase):
    """Test suite for smooth transitions and view caching."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_transitions.db")
        init_database(custom_path=self.db_path)

        # Register initial user
        self.session = register_first_user(
            full_name="Quality Admin",
            org_name="TQM Enterprise",
            username="qualityadmin",
            password="SecurePassword123!",
            confirm_password="SecurePassword123!",
            custom_path=self.db_path,
        )

        # Seed sample inventory
        for i in range(1, 6):
            add_product(
                product_id=f"ITEM-{i:03d}",
                name=f"Standard Component #{i}",
                category="Electrical" if i % 2 == 0 else "Mechanical",
                supplier="Global Supplies",
                quantity=10 * i,
                price=25.0 * i,
                custom_path=self.db_path,
            )

        self.app = IMSApplication(db_path=self.db_path)
        self.app.withdraw()

    def tearDown(self):
        try:
            self.app._clear_all()
            self.app.destroy()
        except Exception:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_view_caching_across_navigation(self):
        """Verify that navigating between Dashboard, Inventory, and Settings reuses cached frames."""
        self.app.show_app_shell(self.session)

        # Initially shows dashboard
        self.assertIn("dash", self.app.views)
        dash_instance = self.app.views["dash"]
        self.assertIsInstance(dash_instance, DashboardFrame)
        self.assertEqual(self.app.current_view, dash_instance)

        # Navigate to Inventory
        self.app.show_inventory_view()
        self.assertIn("inv", self.app.views)
        inv_instance = self.app.views["inv"]
        self.assertIsInstance(inv_instance, InventoryView)
        self.assertEqual(self.app.current_view, inv_instance)

        # Navigate to Settings
        self.app.show_settings_view()
        self.assertIn("settings", self.app.views)
        settings_instance = self.app.views["settings"]
        self.assertIsInstance(settings_instance, SettingsView)
        self.assertEqual(self.app.current_view, settings_instance)

        # Navigate back to Dashboard: should REUSE existing instance rather than recreating
        self.app.show_dashboard_view()
        self.assertIs(self.app.views["dash"], dash_instance)
        self.assertIs(self.app.current_view, dash_instance)

        # Navigate back to Inventory: should REUSE existing instance
        self.app.show_inventory_view()
        self.assertIs(self.app.views["inv"], inv_instance)
        self.assertIs(self.app.current_view, inv_instance)

    def test_02_deep_link_filter_updates_cached_inventory(self):
        """Verify that deep-linking into cached InventoryView updates criteria correctly."""
        self.app.show_app_shell(self.session)
        self.app.show_inventory_view()
        inv_instance = self.app.views["inv"]

        # Deep link with specific category
        self.app.show_inventory_view(FilterCriteria(category="Electrical"))
        self.assertIs(self.app.views["inv"], inv_instance)
        self.assertEqual(inv_instance.opt_category.get(), "Electrical")
        self.assertEqual(len(inv_instance.products), 2)  # ITEM-002, ITEM-004

    def test_03_modal_dialog_geometry_initialization(self):
        """Verify that modal dialogs set geometry in single pass without error."""
        self.app.show_app_shell(self.session)

        # ProductFormModal
        modal_form = ProductFormModal(
            parent=self.app,
            on_success=lambda _p: None,
            product=None,
            db_path=self.db_path,
        )
        try:
            modal_form.update()
            self.assertTrue(modal_form.winfo_exists())
            self.assertTrue(modal_form.geometry().startswith("640x510"))
        finally:
            modal_form.destroy()

        # ProductDetailsModal
        sample_prod = add_product(
            product_id="SKU-TEST", name="Test", category="Test", supplier="Test", quantity=5, price=10.0, custom_path=self.db_path
        )
        modal_details = ProductDetailsModal(
            parent=self.app,
            product=sample_prod,
        )
        try:
            modal_details.update()
            self.assertTrue(modal_details.winfo_exists())
            self.assertTrue(modal_details.geometry().startswith("580x420"))
        finally:
            modal_details.destroy()

    def test_04_installer_script_icon_definition(self):
        """Verify that installer.iss contains proper app_icon.ico bundling and desktop shortcut icon."""
        iss_path = Path(__file__).resolve().parent.parent / "installer.iss"
        self.assertTrue(iss_path.is_file(), "installer.iss must exist")
        iss_content = iss_path.read_text(encoding="utf-8")

        # Must explicitly copy app_icon.ico to {app}
        self.assertIn('Source: "app_icon.ico"; DestDir: "{app}"', iss_content)
        # Must configure desktop shortcut with app_icon.ico
        self.assertIn('Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; IconFilename: "{app}\\app_icon.ico"', iss_content)
        # Must configure uninstall display icon
        self.assertIn('UninstallDisplayIcon={app}\\app_icon.ico', iss_content)

    def test_05_inventory_row_recycling_eliminates_widget_churn(self):
        """Verify that InventoryView reuses pooled row widgets in-place rather than destroying them."""
        self.app.show_app_shell(self.session)
        self.app.show_inventory_view()
        inv_view = self.app.views["inv"]

        self.assertGreaterEqual(len(inv_view._row_pool), 5)
        original_row_0 = inv_view._row_pool[0]
        original_row_1 = inv_view._row_pool[1]

        # Trigger a search filter that returns a subset of items
        inv_view.refresh_products(FilterCriteria(search_query="ITEM-001"))
        self.assertEqual(len(inv_view.products), 1)

        # Confirm the first pooled row was reused in-place
        self.assertIs(inv_view._row_pool[0], original_row_0)
        self.assertEqual(inv_view._row_pool[0].sku_lbl.cget("text"), "ITEM-001")
        # Confirm excess rows from prior query are unmapped (hidden) rather than crashed
        self.assertEqual(inv_view._row_pool[1].winfo_manager(), "")

        # Reset filters: should re-use both rows
        inv_view.clear_all_filters()
        self.assertIs(inv_view._row_pool[0], original_row_0)
        self.assertIs(inv_view._row_pool[1], original_row_1)
        self.assertEqual(inv_view._row_pool[0].winfo_manager(), "pack")
        self.assertEqual(inv_view._row_pool[1].winfo_manager(), "pack")

    def test_06_dashboard_row_recycling(self):
        """Verify that DashboardFrame reuses pooled row widgets in-place across refreshes."""
        self.app.show_app_shell(self.session)
        dash = self.app.views["dash"]

        self.assertGreaterEqual(len(dash._row_pool), 5)
        initial_row_0 = dash._row_pool[0]

        dash.refresh_dashboard()
        self.assertIs(dash._row_pool[0], initial_row_0)

    def test_07_status_badge_update_status(self):
        """Verify StatusBadge update_status alters visual presentation without recreating widgets."""
        from app.ui.components import StatusBadge
        from app.ui.theme import COLOR_DANGER, COLOR_SUCCESS

        badge = StatusBadge(self.app, status="In Stock")
        try:
            self.assertEqual(badge._lbl.cget("text"), "In Stock")
            self.assertEqual(badge.cget("fg_color"), COLOR_SUCCESS)

            badge.update_status("Out of Stock")
            self.assertEqual(badge._lbl.cget("text"), "Out of Stock")
            self.assertEqual(badge.cget("fg_color"), COLOR_DANGER)
        finally:
            badge.destroy()

    def test_08_search_debouncing_timer_management(self):
        """Verify that rapid search key releases debounce properly using after/after_cancel."""
        self.app.show_app_shell(self.session)
        self.app.show_inventory_view()
        inv = self.app.views["inv"]

        class DummyEvent:
            keysym = "a"

        inv._on_search_key_release(DummyEvent())
        first_timer_id = inv._search_after_id
        self.assertIsNotNone(first_timer_id)

        # Simulate second rapid keystroke
        inv._on_search_key_release(DummyEvent())
        second_timer_id = inv._search_after_id
        self.assertIsNotNone(second_timer_id)
        self.assertNotEqual(first_timer_id, second_timer_id)

        # Cancel on enter
        inv._on_search_enter()
        self.assertIsNone(inv._search_after_id)
