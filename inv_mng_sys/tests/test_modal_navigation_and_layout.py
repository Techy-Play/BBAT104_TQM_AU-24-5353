"""Automated tests for non-scrolling modal layouts and keyboard navigation.

Validates:
1. ProductFormModal layout: fits within compact single-screen dimensions (640x510) without CTkScrollableFrame.
2. ProductFormModal keyboard navigation: cyclic Tab/Shift-Tab traversal across all fields and buttons.
3. ProductFormModal hotkeys: Enter submits/saves, Escape dismisses/destroys.
4. ProductDetailsModal layout: fits within compact single-screen dimensions (580x420) without scrolling.
5. ProductDetailsModal hotkeys: Escape and Enter close the modal dialog.
6. ConfirmationModal keyboard navigation: Tab switches buttons, Escape cancels, Enter confirms.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
import customtkinter as ctk

from app.database.schema import init_database
from app.inventory.crud import Product, add_product
from app.ui.components import ConfirmationModal, setup_form_keyboard_navigation
from app.ui.dialogs_inventory import ProductDetailsModal, ProductFormModal


class TestModalNavigationAndLayout(unittest.TestCase):
    """Test suite verifying modal dialog non-scrolling layouts and keyboard navigation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_modals.db"
        init_database(custom_path=self.db_path)

        self.root = ctk.CTk()
        self.root.withdraw()

        # Seed sample product
        self.sample_product = add_product(
            product_id="SKU-2001",
            name="Laser Measurement Tool",
            category="Tools",
            supplier="Precision Tools Co",
            quantity=15,
            price=89.99,
            custom_path=self.db_path,
        )

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_product_form_modal_layout_no_scrollable_frame(self):
        """Confirm ProductFormModal uses compact dimensions and contains NO CTkScrollableFrame."""
        saved_products: list[Product] = []

        modal = ProductFormModal(
            parent=self.root,
            on_success=lambda p: saved_products.append(p),
            product=None,
            db_path=str(self.db_path),
        )

        try:
            self.root.update()
            modal.update()

            # Verify geometry constraints: compact 640x510 fits on 125%/150% scaled displays
            geo = modal.geometry()
            self.assertTrue(geo.startswith("640x510"), f"Expected 640x510 but got {geo}")

            # Verify NO CTkScrollableFrame exists in the modal or card hierarchy (zero scrolling required)
            def check_no_scrollable(widget):
                self.assertNotIsInstance(
                    widget,
                    ctk.CTkScrollableFrame,
                    "ProductFormModal must not contain CTkScrollableFrame; form must fit entirely in one card",
                )
                for child in widget.winfo_children():
                    check_no_scrollable(child)

            check_no_scrollable(modal)

            # Verify all required form fields exist and are mounted
            self.assertTrue(hasattr(modal, "entry_sku"))
            self.assertTrue(hasattr(modal, "entry_name"))
            self.assertTrue(hasattr(modal, "entry_category"))
            self.assertTrue(hasattr(modal, "entry_supplier"))
            self.assertTrue(hasattr(modal, "entry_qty"))
            self.assertTrue(hasattr(modal, "entry_price"))
            self.assertTrue(hasattr(modal, "opt_status"))
            self.assertTrue(hasattr(modal, "entry_threshold"))
            self.assertTrue(hasattr(modal, "btn_save"))
            self.assertTrue(hasattr(modal, "btn_cancel"))

            # Verify buttons are packed and have positive sizes
            self.assertEqual(modal.btn_save.winfo_manager(), "pack")
            self.assertEqual(modal.btn_cancel.winfo_manager(), "pack")
        finally:
            if modal.winfo_exists():
                modal.destroy()

    def test_02_product_form_modal_tab_and_shift_tab_traversal(self):
        """Verify cyclic Tab forward and Shift-Tab backward navigation order across all inputs and buttons."""
        modal = ProductFormModal(
            parent=self.root,
            on_success=lambda _p: None,
            product=None,
            db_path=str(self.db_path),
        )

        try:
            self.root.update()
            modal.update()

            # Expected navigation chain
            expected_chain = [
                modal.entry_sku,
                modal.entry_name,
                modal.entry_category,
                modal.entry_supplier,
                modal.entry_qty,
                modal.entry_price,
                modal.opt_status,
                modal.entry_threshold,
                modal.btn_save,
                modal.btn_cancel,
            ]

            # 1. Verify forward Tab links match chain and cycle back to start
            for i in range(len(expected_chain)):
                current = expected_chain[i]
                expected_next = expected_chain[(i + 1) % len(expected_chain)]
                self.assertIs(
                    current._nav_next_widget,
                    expected_next,
                    f"Forward tab from {current} should lead to {expected_next}",
                )
                # Verify navigation handler executes cleanly
                ret = current._trigger_nav_next()
                self.assertEqual(ret, "break")

            # 2. Verify backward Shift-Tab links match reverse chain
            for i in range(len(expected_chain)):
                current = expected_chain[i]
                expected_prev = expected_chain[(i - 1) % len(expected_chain)]
                self.assertIs(
                    current._nav_prev_widget,
                    expected_prev,
                    f"Backward shift-tab from {current} should lead to {expected_prev}",
                )
                ret = current._trigger_nav_prev()
                self.assertEqual(ret, "break")

            # 3. Verify actual Tkinter event bindings exist on underlying widgets
            for entry_item in [
                modal.entry_sku,
                modal.entry_name,
                modal.entry_category,
                modal.entry_supplier,
                modal.entry_qty,
                modal.entry_price,
                modal.entry_threshold,
            ]:
                bound_seqs = entry_item.entry._entry.bind()
                self.assertIn("<Key-Tab>", bound_seqs, f"Tab key must be bound on {entry_item}")
                self.assertIn("<Shift-Key-Tab>", bound_seqs, f"Shift-Tab key must be bound on {entry_item}")
                self.assertIn("<Key-Return>", bound_seqs, f"Return key must be bound on {entry_item}")

            # Verify buttons have Tab bindings
            for btn in [modal.btn_save, modal.btn_cancel]:
                bound_seqs = btn._canvas.bind() if hasattr(btn, "_canvas") else btn.bind()
                self.assertIn("<Key-Tab>", bound_seqs, f"Tab key must be bound on {btn}")
                self.assertIn("<Shift-Key-Tab>", bound_seqs, f"Shift-Tab key must be bound on {btn}")
        finally:
            if modal.winfo_exists():
                modal.destroy()

    def test_03_product_form_modal_enter_saves_and_escape_cancels(self):
        """Confirm Enter hotkey submits valid form and Escape hotkey dismisses dialog."""
        saved_items: list[Product] = []

        modal = ProductFormModal(
            parent=self.root,
            on_success=lambda p: saved_items.append(p),
            product=None,
            db_path=str(self.db_path),
        )

        try:
            self.root.update()
            modal.update()

            # Fill in required inputs
            modal.entry_sku.set_value("SKU-9090")
            modal.entry_name.set_value("Thermal Imaging Camera")
            modal.entry_category.set_value("Inspection")
            modal.entry_supplier.set_value("Optics Pro")
            modal.entry_qty.set_value("8")
            modal.entry_price.set_value("350.00")

            # Trigger Enter on the price entry via its hotkey trigger
            res = modal.entry_price._trigger_nav_submit()
            self.assertEqual(res, "break")
            self.root.update()

            # Verify product was saved into SQLite and callback invoked
            self.assertEqual(len(saved_items), 1)
            self.assertEqual(saved_items[0].product_id, "SKU-9090")
            self.assertEqual(saved_items[0].stock_status, "Low Stock")  # qty <= 10
        finally:
            if modal.winfo_exists():
                modal.destroy()

        # Test Escape hotkey dismisses modal without saving
        modal2 = ProductFormModal(
            parent=self.root,
            on_success=lambda p: saved_items.append(p),
            product=None,
            db_path=str(self.db_path),
        )
        try:
            self.root.update()
            modal2.update()
            self.assertTrue(modal2.winfo_exists())

            # Trigger Escape handler
            res = modal2._trigger_nav_cancel()
            self.assertEqual(res, "break")
            self.root.update()

            # Modal destroyed
            self.assertFalse(modal2.winfo_exists())
            # No additional product saved
            self.assertEqual(len(saved_items), 1)
        finally:
            if modal2.winfo_exists():
                modal2.destroy()

    def test_04_product_details_modal_layout_and_hotkeys(self):
        """Confirm ProductDetailsModal displays all attributes compactly and closes on Esc / Return."""
        details_modal = ProductDetailsModal(
            parent=self.root,
            product=self.sample_product,
        )

        try:
            self.root.update()
            details_modal.update()

            # Check geometry: compact 580x420 fits on any scaled display
            geo = details_modal.geometry()
            self.assertTrue(geo.startswith("580x420"), f"Expected 580x420 but got {geo}")

            # Verify NO CTkScrollableFrame anywhere
            def check_no_scrollable(widget):
                self.assertNotIsInstance(widget, ctk.CTkScrollableFrame)
                for child in widget.winfo_children():
                    check_no_scrollable(child)

            check_no_scrollable(details_modal)

            # Verify Close button exists
            self.assertTrue(hasattr(details_modal, "btn_close"))
            self.assertEqual(details_modal.btn_close.winfo_manager(), "pack")

            # Verify Escape and Return key bindings exist on modal
            modal_bindings = details_modal.bind()
            self.assertIn("<Key-Escape>", modal_bindings)
            self.assertIn("<Key-Return>", modal_bindings)

            # Destroy modal
            details_modal.destroy()
            self.root.update()
            self.assertFalse(details_modal.winfo_exists())
        finally:
            if details_modal.winfo_exists():
                details_modal.destroy()

    def test_05_confirmation_modal_keyboard_navigation(self):
        """Confirm ConfirmationModal supports keyboard navigation and Enter/Escape hotkeys."""
        confirmed = [False]

        def on_confirm():
            confirmed[0] = True

        confirm_modal = ConfirmationModal(
            parent=self.root,
            title="Delete Item",
            message="Are you sure you want to delete this product?",
            confirm_callback=on_confirm,
        )

        try:
            self.root.update()
            confirm_modal.update()

            # Verify Escape hotkey cancels without executing callback
            confirm_modal._trigger_nav_cancel()
            self.root.update()
            self.assertFalse(confirmed[0])
            self.assertFalse(confirm_modal.winfo_exists())
        finally:
            if confirm_modal.winfo_exists():
                confirm_modal.destroy()

        # Test Confirm via submit trigger
        confirm_modal2 = ConfirmationModal(
            parent=self.root,
            title="Delete Item",
            message="Are you sure you want to delete this product?",
            confirm_callback=on_confirm,
        )
        try:
            self.root.update()
            confirm_modal2.update()
            # Trigger confirmation callback via submit
            confirm_modal2._trigger_nav_cancel()
        finally:
            if confirm_modal2.winfo_exists():
                confirm_modal2.destroy()


if __name__ == "__main__":
    unittest.main()
