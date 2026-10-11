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
)
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
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
        self.on_success = on_success
        self.product = product
        self.db_path = db_path
        self.is_edit = product is not None

        title_text = "Edit Inventory Product" if self.is_edit else "Add New Inventory Product"
        self.title(title_text)
        self.geometry("520x640")
        self.minsize(480, 600)
        self.transient(parent)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 260
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 320
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self._build_ui(title_text)

    def _build_ui(self, title_text: str) -> None:
        scroll_card = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_card.pack(fill="both", expand=True, padx=20, pady=20)

        card = CardFrame(scroll_card)
        card.pack(fill="both", expand=True, padx=4, pady=4)

        # Header
        header = ctk.CTkLabel(card, text=title_text, font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY)
        header.pack(anchor="w", padx=24, pady=(20, 4))

        sub = ctk.CTkLabel(
            card,
            text="Enter product details. All fields are stored persistently in SQLite."
            if not self.is_edit
            else f"Modifying details for SKU: {self.product.product_id}",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        sub.pack(anchor="w", padx=24, pady=(0, 16))

        # Fields
        self.entry_sku = LabeledEntry(
            card,
            label_text="Product ID / SKU *",
            placeholder="e.g. SKU-1001 or BAR-902",
            width=400,
        )
        self.entry_sku.pack(padx=24, pady=5)

        self.entry_name = LabeledEntry(
            card,
            label_text="Product Name *",
            placeholder="e.g. Wireless Barcode Scanner",
            width=400,
        )
        self.entry_name.pack(padx=24, pady=5)

        self.entry_category = LabeledEntry(
            card,
            label_text="Category *",
            placeholder="e.g. Electronics, Tools, Hardware",
            width=400,
        )
        self.entry_category.pack(padx=24, pady=5)

        self.entry_supplier = LabeledEntry(
            card,
            label_text="Supplier *",
            placeholder="e.g. Global Tech Supplies Ltd.",
            width=400,
        )
        self.entry_supplier.pack(padx=24, pady=5)

        # Numeric row: Quantity and Price side-by-side
        num_frame = ctk.CTkFrame(card, fg_color="transparent")
        num_frame.pack(fill="x", padx=24, pady=5)
        num_frame.grid_columnconfigure((0, 1), weight=1)

        self.entry_qty = LabeledEntry(
            num_frame,
            label_text="Quantity *",
            placeholder="e.g. 50",
            width=180,
        )
        self.entry_qty.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.entry_price = LabeledEntry(
            num_frame,
            label_text="Unit Price ($) *",
            placeholder="e.g. 29.99",
            width=180,
        )
        self.entry_price.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        # Stock Status option menu
        status_frame = ctk.CTkFrame(card, fg_color="transparent")
        status_frame.pack(fill="x", padx=24, pady=5)

        status_lbl = ctk.CTkLabel(
            status_frame,
            text="Stock Status (Auto-calculated if omitted)",
            font=FONT_BODY,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        status_lbl.pack(fill="x", pady=(0, 4))

        self.opt_status = ctk.CTkOptionMenu(
            status_frame,
            values=["Auto (Recommended)", "In Stock", "Low Stock", "Out of Stock"],
            height=36,
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

        # Feedback banner
        self.banner = MessageBanner(card)
        self.banner.pack(padx=24, pady=(10, 4))

        # Buttons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(12, 24))

        btn_cancel = SecondaryButton(btn_row, text="Cancel", command=self.destroy, width=120)
        btn_cancel.pack(side="right", padx=(10, 0))

        btn_save_text = "Save Changes" if self.is_edit else "Add Product"
        self.btn_save = PrimaryButton(btn_row, text=btn_save_text, command=self._handle_save, width=160)
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
        self.product = product
        self.title(f"Product Details — {product.product_id}")
        self.geometry("480x520")
        self.minsize(460, 500)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 240
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 260
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        card = CardFrame(self)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with SKU and Status
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(20, 8))

        name_lbl = ctk.CTkLabel(
            top_row,
            text=product.name,
            font=FONT_HEADING,
            text_color=COLOR_TEXT_PRIMARY,
            wraplength=310,
            justify="left",
        )
        name_lbl.pack(side="left")

        badge = StatusBadge(top_row, status=product.stock_status)
        badge.pack(side="right")

        sku_sub = ctk.CTkLabel(card, text=f"Product SKU: {product.product_id}", font=FONT_BODY, text_color=COLOR_TEXT_MUTED)
        sku_sub.pack(anchor="w", padx=20, pady=(0, 18))

        # Attributes Table
        details = [
            ("Category", product.category),
            ("Supplier", product.supplier),
            ("In-Stock Quantity", str(product.quantity)),
            ("Unit Price", f"${product.price:.2f}"),
            ("Total Stock Value", f"${product.total_value:,.2f}"),
            ("Stock Status", product.stock_status),
            ("Created Timestamp", product.created_at),
            ("Last Updated", product.updated_at),
        ]

        for label, val in details:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            lbl = ctk.CTkLabel(row, text=f"{label}:", font=FONT_BODY, text_color=COLOR_TEXT_MUTED, width=150, anchor="w")
            lbl.pack(side="left")
            val_lbl = ctk.CTkLabel(row, text=val, font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, anchor="w")
            val_lbl.pack(side="left")

        # Close button
        btn_close = SecondaryButton(card, text="Close", command=self.destroy, width=120)
        btn_close.pack(anchor="e", padx=20, pady=(24, 20))
