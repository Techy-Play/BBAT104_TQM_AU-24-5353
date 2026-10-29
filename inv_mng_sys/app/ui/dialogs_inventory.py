"""Product form (Add/Edit) and details modal dialogs."""

from __future__ import annotations

import logging
from typing import Callable, Optional
import customtkinter as ctk

from app.inventory.crud import (
    Product,
    add_product,
    update_product,
)
from app.ui.components import (
    CardFrame,
    LabeledEntry,
    MessageBanner,
    PrimaryButton,
    SecondaryButton,
    StatusBadge,
    setup_form_keyboard_navigation,
)
from app.ui.theme import (
    COLOR_BORDER,
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
)

logger = logging.getLogger(__name__)


class ProductFormModal(ctk.CTkToplevel):
    """Modal dialog for creating a new product or editing an existing one."""

    def __init__(
        self,
        parent,
        on_success: Callable[[Product], None],
        product: Optional[Product] = None,
        db_path: Optional[str] = None,
    ):
        super().__init__(parent)
        self.withdraw()  # Prevent unstyled flash during layout construction
        self.on_success = on_success
        self.product = product
        self.db_path = db_path
        self.is_edit = product is not None

        title_text = "Edit Inventory Product" if self.is_edit else "Add New Inventory Product"
        self.title(title_text)
        width, height = 640, 510
        self.minsize(580, 470)
        self.resizable(True, True)
        self.transient(parent)

        # Center on parent window in single atomic geometry calculation
        try:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            pos_x = max(0, parent_x + (parent_w - width) // 2)
            pos_y = max(0, parent_y + (parent_h - height) // 2)
            self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        except Exception:
            self.geometry(f"{width}x{height}")

        self._build_ui(title_text)
        self.deiconify()
        self.grab_set()

    def _build_ui(self, title_text: str) -> None:
        # Direct CardFrame without CTkScrollableFrame to eliminate scrolling completely
        card = CardFrame(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header Row
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(16, 4))

        title_icon = "✏️ " if self.is_edit else "➕ "
        header = ctk.CTkLabel(
            header_frame,
            text=f"{title_icon}{title_text}",
            font=FONT_HEADING,
            text_color=COLOR_TEXT_PRIMARY,
        )
        header.pack(side="left")

        if self.is_edit and self.product:
            sku_badge = ctk.CTkLabel(
                header_frame,
                text=f"SKU: {self.product.product_id}",
                font=FONT_SMALL,
                text_color=COLOR_PRIMARY[1] if isinstance(COLOR_PRIMARY, tuple) else COLOR_PRIMARY,
            )
            sku_badge.pack(side="right")

        sub = ctk.CTkLabel(
            card,
            text="Enter product attributes below. Press Tab to switch fields, Enter to save."
            if not self.is_edit
            else f"Modifying attributes for '{self.product.name}'. Press Enter to save.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        sub.pack(anchor="w", padx=20, pady=(0, 10))

        # 2-Column Responsive Form Grid (All fields visible at once without scrolling)
        form_grid = ctk.CTkFrame(card, fg_color="transparent")
        form_grid.pack(fill="x", padx=20, pady=(0, 4))
        form_grid.grid_columnconfigure((0, 1), weight=1, uniform="form_col")

        # Row 0: SKU and Product Name
        self.entry_sku = LabeledEntry(
            form_grid,
            label_text="Product ID / SKU *",
            placeholder="e.g. SKU-1001",
            width=260,
        )
        self.entry_sku.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)

        self.entry_name = LabeledEntry(
            form_grid,
            label_text="Product Name *",
            placeholder="e.g. Wireless Barcode Scanner",
            width=260,
        )
        self.entry_name.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Row 1: Category and Supplier
        self.entry_category = LabeledEntry(
            form_grid,
            label_text="Category *",
            placeholder="e.g. Electronics, Tools",
            width=260,
        )
        self.entry_category.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)

        self.entry_supplier = LabeledEntry(
            form_grid,
            label_text="Supplier *",
            placeholder="e.g. Global Tech Supplies",
            width=260,
        )
        self.entry_supplier.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Row 2: Quantity and Unit Price
        self.entry_qty = LabeledEntry(
            form_grid,
            label_text="Quantity (units) *",
            placeholder="e.g. 50",
            width=260,
        )
        self.entry_qty.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=4)

        self.entry_price = LabeledEntry(
            form_grid,
            label_text="Unit Price ($) *",
            placeholder="e.g. 29.99",
            width=260,
        )
        self.entry_price.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Row 3: Stock Status and Help Rule Box
        status_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        status_frame.grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=4)

        status_lbl = ctk.CTkLabel(
            status_frame,
            text="Stock Status (Auto-calculated if omitted)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        status_lbl.pack(fill="x", pady=(0, 4))

        self.opt_status = ctk.CTkOptionMenu(
            status_frame,
            values=["Auto (Recommended)", "In Stock", "Low Stock", "Out of Stock"],
            height=34,
            font=FONT_BODY,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY_HOVER,
            button_hover_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_PRIMARY,
        )
        self.opt_status.pack(fill="x")

        # Auto rule callout box
        rule_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        rule_frame.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=4)

        rule_lbl = ctk.CTkLabel(
            rule_frame,
            text="Threshold Status Rule (Q13 Automation)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        rule_lbl.pack(fill="x", pady=(0, 4))

        rule_box = ctk.CTkFrame(rule_frame, fg_color=COLOR_SECONDARY, height=34, corner_radius=6)
        rule_box.pack(fill="x")
        rule_box.pack_propagate(False)

        rule_text = ctk.CTkLabel(
            rule_box,
            text="Qty ≤ 10 → Low Stock  |  Qty = 0 → Out of Stock",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        rule_text.pack(expand=True)

        # Feedback banner
        self.banner = MessageBanner(card)
        self.banner.pack(fill="x", padx=20, pady=(4, 2))

        # Permanent, Non-scrolling Action Footer
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", padx=20, pady=(6, 16))

        hint_kb = ctk.CTkLabel(
            btn_row,
            text="⌨️ Tab: Next field • Shift+Tab: Prev • Enter: Save • Esc: Cancel",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        hint_kb.pack(side="left")

        self.btn_cancel = SecondaryButton(btn_row, text="Cancel", command=self.destroy, width=100, height=34)
        self.btn_cancel.pack(side="right", padx=(10, 0))

        btn_save_text = "Save Changes" if self.is_edit else "Add Product"
        self.btn_save = PrimaryButton(btn_row, text=btn_save_text, command=self._handle_save, width=140, height=34)
        self.btn_save.pack(side="right")

        # Pre-populate if editing
        if self.is_edit and self.product:
            self.entry_sku.set_value(self.product.product_id)
            self.entry_name.set_value(self.product.name)
            self.entry_category.set_value(self.product.category)
            self.entry_supplier.set_value(self.product.supplier)
            self.entry_qty.set_value(str(self.product.quantity))
            self.entry_price.set_value(f"{self.product.price:.2f}")
            if self.product.stock_status in ("In Stock", "Low Stock", "Out of Stock"):
                self.opt_status.set(self.product.stock_status)

        # Fast keyboard navigation & hotkeys
        setup_form_keyboard_navigation(
            widgets=[
                self.entry_sku,
                self.entry_name,
                self.entry_category,
                self.entry_supplier,
                self.entry_qty,
                self.entry_price,
                self.opt_status,
                self.btn_save,
                self.btn_cancel,
            ],
            on_submit=self._handle_save,
            on_cancel=self.destroy,
            toplevel=self,
        )

        self.btn_save.bind("<Return>", lambda _e: (self._handle_save(), "break")[1])
        self.btn_save.bind("<space>", lambda _e: (self._handle_save(), "break")[1])
        self.btn_cancel.bind("<Return>", lambda _e: (self.destroy(), "break")[1])
        self.btn_cancel.bind("<space>", lambda _e: (self.destroy(), "break")[1])

        # Immediate initial focus for instant typing
        target_focus = self.entry_name if (self.is_edit and self.entry_sku.get_value()) else self.entry_sku
        self._focus_after_id = self.after(50, target_focus.focus)

    def destroy(self):
        try:
            if hasattr(self, "_focus_after_id") and self._focus_after_id:
                self.after_cancel(self._focus_after_id)
        except Exception:
            pass
        super().destroy()

    def _handle_save(self) -> None:
        self.banner.clear()

        sku = self.entry_sku.get_value()
        name = self.entry_name.get_value()
        category = self.entry_category.get_value()
        supplier = self.entry_supplier.get_value()
        qty = self.entry_qty.get_value()
        price = self.entry_price.get_value()
        status_choice = self.opt_status.get()
        explicit_status = None if "Auto" in status_choice else status_choice

        try:
            if self.is_edit and self.product:
                saved = update_product(
                    item_id=self.product.id,
                    product_id=sku,
                    name=name,
                    category=category,
                    supplier=supplier,
                    quantity=qty,
                    price=price,
                    stock_status=explicit_status,
                    custom_path=self.db_path,
                )
            else:
                saved = add_product(
                    product_id=sku,
                    name=name,
                    category=category,
                    supplier=supplier,
                    quantity=qty,
                    price=price,
                    stock_status=explicit_status,
                    custom_path=self.db_path,
                )

            self.on_success(saved)
            self.destroy()
        except ValueError as err:
            self.banner.show_error(str(err))
        except Exception as exc:
            logger.exception("Error saving product.")
            self.banner.show_error(f"Failed to save product: {exc}")


class ProductDetailsModal(ctk.CTkToplevel):
    """Modal dialog displaying comprehensive product details and valuation."""

    def __init__(self, parent, product: Product):
        super().__init__(parent)
        self.withdraw()  # Prevent unstyled flash during layout construction
        self.product = product
        self.title(f"Product Details — {product.product_id}")
        width, height = 580, 420
        self.minsize(520, 380)
        self.resizable(True, True)
        self.transient(parent)

        # Center on parent in single atomic geometry calculation
        try:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            pos_x = max(0, parent_x + (parent_w - width) // 2)
            pos_y = max(0, parent_y + (parent_h - height) // 2)
            self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        except Exception:
            self.geometry(f"{width}x{height}")

        card = CardFrame(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header with SKU and Status
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(16, 4))

        name_lbl = ctk.CTkLabel(
            top_row,
            text=f"📦 {product.name}",
            font=FONT_HEADING,
            text_color=COLOR_TEXT_PRIMARY,
            wraplength=380,
            justify="left",
        )
        name_lbl.pack(side="left")

        badge = StatusBadge(top_row, status=product.stock_status)
        badge.pack(side="right")

        sku_sub = ctk.CTkLabel(
            card,
            text=f"Product SKU: {product.product_id} • Offline Local SQLite Record",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        sku_sub.pack(anchor="w", padx=20, pady=(0, 14))

        # 2-Column Attributes Grid (clean, non-scrolling)
        grid_frame = ctk.CTkFrame(card, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        grid_frame.grid_columnconfigure((0, 1), weight=1, uniform="col_detail")

        left_details = [
            ("Category", product.category),
            ("Supplier", product.supplier),
            ("In-Stock Quantity", f"{product.quantity:,} units"),
            ("Unit Price", f"${product.price:.2f}"),
        ]

        right_details = [
            ("Total Valuation", f"${product.total_value:,.2f}"),
            ("Stock Status", product.stock_status),
            ("Created Date", product.created_at[:16] if product.created_at else "N/A"),
            ("Last Updated", product.updated_at[:16] if product.updated_at else "N/A"),
        ]

        # Left Column Box
        left_box = ctk.CTkFrame(grid_frame, fg_color=COLOR_SECONDARY, corner_radius=6)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=2)
        for label, val in left_details:
            row = ctk.CTkFrame(left_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(row, text=f"{label}:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")

        # Right Column Box
        right_box = ctk.CTkFrame(grid_frame, fg_color=COLOR_SECONDARY, corner_radius=6)
        right_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=2)
        for label, val in right_details:
            row = ctk.CTkFrame(right_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(row, text=f"{label}:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")

        # Footer Action Bar
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", padx=20, pady=(6, 16))

        hint_kb = ctk.CTkLabel(
            btn_row,
            text="⌨️ Esc / Enter: Close dialog",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        hint_kb.pack(side="left")

        self.btn_close = SecondaryButton(btn_row, text="Close", command=self.destroy, width=110, height=34)
        self.btn_close.pack(side="right")

        # Hotkeys
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self.destroy())
        self.btn_close.bind("<Return>", lambda _e: (self.destroy(), "break")[1])
        self.btn_close.bind("<space>", lambda _e: (self.destroy(), "break")[1])

        self._focus_after_id = self.after(50, self.btn_close.focus_set)
        self.deiconify()
        self.grab_set()

    def destroy(self):
        try:
            if hasattr(self, "_focus_after_id") and self._focus_after_id:
                self.after_cancel(self._focus_after_id)
                self._focus_after_id = None
        except Exception:
            pass
        super().destroy()

