"""Inventory management view: product listing, quick-search, and CRUD triggers."""

from __future__ import annotations

import logging
from typing import Callable, List, Optional
import customtkinter as ctk

from app.inventory.crud import (
    Product,
    delete_product,
    get_all_products,
)
from app.ui.components import (
    CardFrame,
    ConfirmationModal,
    DangerButton,
    PrimaryButton,
    SecondaryButton,
    StatusBadge,
)
from app.ui.dialogs_inventory import ProductDetailsModal, ProductFormModal
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_ROW_ALT,
    COLOR_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_TABLE_HEADER,
)

logger = logging.getLogger(__name__)


class InventoryView(ctk.CTkFrame):
    """Full inventory management screen with table, search, and CRUD actions."""

    def __init__(
        self,
        master,
        on_data_changed: Optional[Callable[[], None]] = None,
        db_path: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_data_changed = on_data_changed
        self.db_path = db_path
        self.products: List[Product] = []

        self._build_ui()
        self.refresh_products()

    def _build_ui(self) -> None:
        # Top action toolbar
        toolbar = CardFrame(self)
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=12)

        title = ctk.CTkLabel(title_box, text="📦 Inventory Management", font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY)
        title.pack(anchor="w")

        sub = ctk.CTkLabel(
            title_box,
            text="Add, inspect, edit, and maintain persistent offline stock records.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        sub.pack(anchor="w")

        btn_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_box.pack(side="right", padx=16, pady=12)

        self.btn_add = PrimaryButton(
            btn_box,
            text="➕ Add Product",
            command=self._open_add_modal,
            width=140,
        )
        self.btn_add.pack(side="left", padx=(0, 8))

        self.btn_refresh = SecondaryButton(
            btn_box,
            text="🔄 Refresh",
            command=self.refresh_products,
            width=100,
        )
        self.btn_refresh.pack(side="left")

        # Search Bar card
        search_card = CardFrame(self)
        search_card.pack(fill="x", padx=20, pady=(0, 10))

        search_row = ctk.CTkFrame(search_card, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search by SKU, Product Name, Category, or Supplier...",
            height=38,
            corner_radius=8,
            font=FONT_BODY,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._handle_search())

        btn_search = PrimaryButton(search_row, text="Search", command=self._handle_search, width=100)
        btn_search.pack(side="left", padx=(0, 8))

        btn_clear = SecondaryButton(search_row, text="Clear", command=self._clear_search, width=80)
        btn_clear.pack(side="left")

        # Result count label
        self.count_lbl = ctk.CTkLabel(
            self,
            text="Loading records...",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        self.count_lbl.pack(fill="x", padx=24, pady=(0, 6))

        # Table container
        self.table_container = CardFrame(self)
        self.table_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Table Header
        self._build_table_header()

        # Scrollable table body
        self.table_body = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.table_body.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_table_header(self) -> None:
        header_frame = ctk.CTkFrame(self.table_container, fg_color=("gray85", "gray20"), height=36, corner_radius=6)
        header_frame.pack(fill="x", padx=8, pady=(8, 4))
        header_frame.pack_propagate(False)

        cols = [
            ("SKU / ID", 110),
            ("Product Name", 200),
            ("Category", 120),
            ("Supplier", 130),
            ("Quantity", 80),
            ("Price", 80),
            ("Status", 110),
            ("Actions", 160),
        ]

        for col_name, width in cols:
            lbl = ctk.CTkLabel(
                header_frame,
                text=col_name,
                font=FONT_TABLE_HEADER,
                text_color=COLOR_TEXT_PRIMARY,
                width=width,
                anchor="w" if col_name != "Actions" else "center",
            )
            lbl.pack(side="left", padx=4)

    def _handle_search(self) -> None:
        query = self.search_entry.get().strip()
        self.refresh_products(search_term=query)

    def _clear_search(self) -> None:
        self.search_entry.delete(0, "end")
        self.refresh_products(search_term="")

    def refresh_products(self, search_term: Optional[str] = None) -> None:
        """Fetch records from SQLite and render table rows."""
        # Clear existing rows in table body
        for child in self.table_body.winfo_children():
            child.destroy()

        term = search_term if search_term is not None else self.search_entry.get().strip()
        try:
            self.products = get_all_products(search_query=term, custom_path=self.db_path)
            total_count = len(self.products)

            if term:
                self.count_lbl.configure(text=f"Showing {total_count} matching product(s) for '{term}'")
            else:
                self.count_lbl.configure(text=f"Showing all {total_count} inventory product(s)")

            if not self.products:
                self._render_empty_state()
                return

            # Render rows
            for idx, prod in enumerate(self.products):
                self._render_row(prod, is_alt=(idx % 2 == 1))

        except Exception as exc:
            logger.exception("Error loading products.")
            self.count_lbl.configure(text="Error loading products from database.")

    def _render_empty_state(self) -> None:
        empty_box = ctk.CTkFrame(self.table_body, fg_color="transparent")
        empty_box.pack(expand=True, fill="both", pady=40)

        icon = ctk.CTkLabel(empty_box, text="📦", font=(FONT_BODY[0], 42))
        icon.pack(pady=(10, 4))

        msg = ctk.CTkLabel(
            empty_box,
            text="No inventory products found.",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        )
        msg.pack()

        tip = ctk.CTkLabel(
            empty_box,
            text="Click '+ Add Product' above to register your first inventory item.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        tip.pack(pady=(4, 16))

        btn = PrimaryButton(empty_box, text="Add Product Now", command=self._open_add_modal, width=160)
        btn.pack()

    def _render_row(self, prod: Product, is_alt: bool) -> None:
        bg_col = COLOR_ROW_ALT if is_alt else "transparent"
        row = ctk.CTkFrame(self.table_body, fg_color=bg_col, corner_radius=6, height=44)
        row.pack(fill="x", pady=2, padx=4)
        row.pack_propagate(False)

        # SKU
        sku_lbl = ctk.CTkLabel(row, text=prod.product_id, font=FONT_BODY, width=110, anchor="w")
        sku_lbl.pack(side="left", padx=4)

        # Name
        name_lbl = ctk.CTkLabel(row, text=prod.name, font=FONT_BODY, width=200, anchor="w")
        name_lbl.pack(side="left", padx=4)

        # Category
        cat_lbl = ctk.CTkLabel(row, text=prod.category, font=FONT_BODY, width=120, anchor="w", text_color=COLOR_TEXT_MUTED)
        cat_lbl.pack(side="left", padx=4)

        # Supplier
        sup_lbl = ctk.CTkLabel(row, text=prod.supplier, font=FONT_BODY, width=130, anchor="w", text_color=COLOR_TEXT_MUTED)
        sup_lbl.pack(side="left", padx=4)

        # Quantity
        qty_lbl = ctk.CTkLabel(row, text=str(prod.quantity), font=FONT_BODY, width=80, anchor="w")
        qty_lbl.pack(side="left", padx=4)

        # Price
        price_lbl = ctk.CTkLabel(row, text=f"${prod.price:.2f}", font=FONT_BODY, width=80, anchor="w")
        price_lbl.pack(side="left", padx=4)

        # Status badge container
        status_box = ctk.CTkFrame(row, fg_color="transparent", width=110)
        status_box.pack(side="left", padx=4)
        status_box.pack_propagate(False)
        badge = StatusBadge(status_box, status=prod.stock_status)
        badge.pack(side="left", pady=8)

        # Action buttons
        act_box = ctk.CTkFrame(row, fg_color="transparent", width=160)
        act_box.pack(side="left", padx=4)
        act_box.pack_propagate(False)

        btn_view = ctk.CTkButton(
            act_box,
            text="👁️",
            width=32,
            height=30,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            hover_color=("gray75", "gray35"),
            command=lambda p=prod: self._view_details(p),
        )
        btn_view.pack(side="left", padx=2)

        btn_edit = ctk.CTkButton(
            act_box,
            text="✏️",
            width=32,
            height=30,
            corner_radius=6,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY[1],
            command=lambda p=prod: self._edit_product(p),
        )
        btn_edit.pack(side="left", padx=2)

        btn_del = ctk.CTkButton(
            act_box,
            text="🗑️",
            width=32,
            height=30,
            corner_radius=6,
            fg_color=("gray70", "gray30"),
            hover_color=("#dc2626", "#dc2626"),
            command=lambda p=prod: self._confirm_delete(p),
        )
        btn_del.pack(side="left", padx=2)

    def _open_add_modal(self) -> None:
        ProductFormModal(
            parent=self.winfo_toplevel(),
            on_success=self._on_product_mutated,
            product=None,
            db_path=self.db_path,
        )

    def _edit_product(self, product: Product) -> None:
        ProductFormModal(
            parent=self.winfo_toplevel(),
            on_success=self._on_product_mutated,
            product=product,
            db_path=self.db_path,
        )

    def _view_details(self, product: Product) -> None:
        ProductDetailsModal(parent=self.winfo_toplevel(), product=product)

    def _confirm_delete(self, product: Product) -> None:
        msg = f"Are you sure you want to delete product '{product.name}' (SKU: {product.product_id})?\n\nThis will permanently remove the record from SQLite."
        ConfirmationModal(
            parent=self.winfo_toplevel(),
            title="Delete Product Confirmation",
            message=msg,
            confirm_text="Delete Product",
            confirm_callback=lambda: self._execute_delete(product.id),
            danger=True,
        )

    def _execute_delete(self, item_id: int) -> None:
        try:
            delete_product(item_id, custom_path=self.db_path)
            self._on_product_mutated(None)
        except Exception as exc:
            logger.exception("Failed to delete product ID %d.", item_id)

    def _on_product_mutated(self, _saved: Optional[Product]) -> None:
        """Called when a product was added, updated, or deleted."""
        self.refresh_products()
        if self.on_data_changed:
            self.on_data_changed()
