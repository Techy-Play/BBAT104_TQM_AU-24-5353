"""Inventory management view: product listing, Q13 search filters, sorting, and CRUD actions."""

from __future__ import annotations

import logging
from typing import Callable, List, Optional
import customtkinter as ctk

from app.inventory.crud import (
    Product,
    delete_product,
)
from app.inventory.filters import (
    FilterCriteria,
    filter_products,
    get_distinct_categories,
    get_distinct_suppliers,
)
from app.settings.settings import SettingsService
from app.ui.components import (
    CardFrame,
    ConfirmationModal,
    DangerButton,
    PrimaryButton,
    SecondaryButton,
    StatusBadge,
    setup_form_keyboard_navigation,
)
from app.ui.dialogs_inventory import ProductDetailsModal, ProductFormModal
from app.ui.theme import (
    COLOR_BORDER,
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_ROW_ALT,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_TABLE_HEADER,
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


class InventoryTableRow(ctk.CTkFrame):
    """Pooled table row widget reused across refreshes to eliminate widget churn and redraw flicker."""

    def __init__(
        self,
        master,
        on_view: Callable[[Product], None],
        on_edit: Callable[[Product], None],
        on_delete: Callable[[Product], None],
    ):
        super().__init__(master, corner_radius=6, height=44)
        self.pack_propagate(False)
        self._on_view = on_view
        self._on_edit = on_edit
        self._on_delete = on_delete
        self.product: Optional[Product] = None

        # SKU
        self.sku_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=110, anchor="w")
        self.sku_lbl.pack(side="left", padx=4)

        # Name
        self.name_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=200, anchor="w")
        self.name_lbl.pack(side="left", padx=4)

        # Category
        self.cat_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=120, anchor="w", text_color=COLOR_TEXT_MUTED)
        self.cat_lbl.pack(side="left", padx=4)

        # Supplier
        self.sup_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=130, anchor="w", text_color=COLOR_TEXT_MUTED)
        self.sup_lbl.pack(side="left", padx=4)

        # Quantity
        self.qty_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=80, anchor="w")
        self.qty_lbl.pack(side="left", padx=4)

        # Price
        self.price_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=80, anchor="w")
        self.price_lbl.pack(side="left", padx=4)

        # Status badge container
        status_box = ctk.CTkFrame(self, fg_color="transparent", width=110)
        status_box.pack(side="left", padx=4)
        status_box.pack_propagate(False)
        self.badge = StatusBadge(status_box, status="In Stock")
        self.badge.pack(side="left", pady=8)

        # Action buttons container
        act_box = ctk.CTkFrame(self, fg_color="transparent", width=160)
        act_box.pack(side="left", padx=4)
        act_box.pack_propagate(False)

        self.btn_view = SecondaryButton(
            act_box,
            text="👁️",
            width=34,
            height=30,
            command=self._handle_view,
        )
        self.btn_view.pack(side="left", padx=2)

        self.btn_edit = PrimaryButton(
            act_box,
            text="✏️",
            width=34,
            height=30,
            command=self._handle_edit,
        )
        self.btn_edit.pack(side="left", padx=2)

        self.btn_del = DangerButton(
            act_box,
            text="🗑️",
            width=34,
            height=30,
            command=self._handle_delete,
        )
        self.btn_del.pack(side="left", padx=2)

    def _handle_view(self) -> None:
        if self.product:
            self._on_view(self.product)

    def _handle_edit(self) -> None:
        if self.product:
            self._on_edit(self.product)

    def _handle_delete(self) -> None:
        if self.product:
            self._on_delete(self.product)

    def update_product(self, prod: Product, is_alt: bool, currency_sym: str = "₹") -> None:
        """Update row contents in-place without widget reconstruction."""
        self.product = prod
        bg_col = COLOR_ROW_ALT if is_alt else "transparent"
        self.configure(fg_color=bg_col)
        self.sku_lbl.configure(text=prod.product_id)
        self.name_lbl.configure(text=prod.name)
        self.cat_lbl.configure(text=prod.category)
        self.sup_lbl.configure(text=prod.supplier)
        self.qty_lbl.configure(text=str(prod.quantity))
        self.price_lbl.configure(text=f"{currency_sym}{prod.price:.2f}")
        self.badge.update_status(prod.stock_status)


class InventoryView(ctk.CTkFrame):
    """Full inventory management screen with table, Q13 search filters, sorting, and CRUD."""

    def __init__(
        self,
        master,
        on_data_changed: Optional[Callable[[], None]] = None,
        db_path: Optional[str] = None,
        initial_criteria: Optional[FilterCriteria] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_data_changed = on_data_changed
        self.db_path = db_path
        self.products: List[Product] = []
        self._row_pool: list[InventoryTableRow] = []
        self._empty_box: Optional[ctk.CTkFrame] = None
        self._cached_categories: Optional[list[str]] = None
        self._cached_suppliers: Optional[list[str]] = None
        self._search_after_id: Optional[str] = None

        self._build_ui()
        if initial_criteria is not None:
            self.apply_initial_criteria(initial_criteria)
        else:
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
            text="Fast Search & Retrieval • Multi-Attribute Filters • Whitelist Sorting",
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

        # Q13 Search & Filter Card
        filter_card = CardFrame(self)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        # Search row
        search_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=(12, 8))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search across Product ID, Name, Category, or Supplier...",
            height=38,
            corner_radius=8,
            font=FONT_BODY,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)
        self.search_entry.bind("<Return>", lambda e: self._on_search_enter())

        btn_search = PrimaryButton(search_row, text="Search", command=self.apply_filters, width=100)
        btn_search.pack(side="left", padx=(0, 8))

        btn_clear = SecondaryButton(search_row, text="Clear All", command=self.clear_all_filters, width=90)
        btn_clear.pack(side="left")

        # Filter and Sort row
        options_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        options_row.pack(fill="x", padx=16, pady=(0, 12))

        # Category Filter
        ctk.CTkLabel(options_row, text="Category:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.opt_category = ctk.CTkOptionMenu(
            options_row,
            values=["All Categories"],
            height=32,
            width=135,
            font=FONT_SMALL,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY_HOVER,
            button_hover_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_PRIMARY,
            command=lambda _val: self.apply_filters(),
        )
        self.opt_category.pack(side="left", padx=(0, 10))

        # Supplier Filter
        ctk.CTkLabel(options_row, text="Supplier:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.opt_supplier = ctk.CTkOptionMenu(
            options_row,
            values=["All Suppliers"],
            height=32,
            width=135,
            font=FONT_SMALL,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY_HOVER,
            button_hover_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_PRIMARY,
            command=lambda _val: self.apply_filters(),
        )
        self.opt_supplier.pack(side="left", padx=(0, 10))

        # Stock Status Filter
        ctk.CTkLabel(options_row, text="Status:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.opt_status = ctk.CTkOptionMenu(
            options_row,
            values=["All Statuses", "In Stock", "Low Stock", "Out of Stock"],
            height=32,
            width=115,
            font=FONT_SMALL,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY_HOVER,
            button_hover_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_PRIMARY,
            command=lambda _val: self.apply_filters(),
        )
        self.opt_status.pack(side="left", padx=(0, 12))

        # Sort By Column
        ctk.CTkLabel(options_row, text="Sort By:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.opt_sort_col = ctk.CTkOptionMenu(
            options_row,
            values=[
                "Last Updated",
                "Product ID",
                "Product Name",
                "Category",
                "Supplier",
                "Quantity",
                "Price",
                "Stock Status",
            ],
            height=32,
            width=125,
            font=FONT_SMALL,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY_HOVER,
            button_hover_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_PRIMARY,
            command=lambda _val: self.apply_filters(),
        )
        self.opt_sort_col.pack(side="left", padx=(0, 8))

        # Sort Direction
        self.opt_sort_dir = ctk.CTkOptionMenu(
            options_row,
            values=["Descending", "Ascending"],
            height=32,
            width=105,
            font=FONT_SMALL,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY_HOVER,
            button_hover_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_PRIMARY,
            command=lambda _val: self.apply_filters(),
        )
        self.opt_sort_dir.pack(side="left")

        # Setup Tab navigation across search and filter options
        setup_form_keyboard_navigation(
            widgets=[
                self.search_entry,
                btn_search,
                btn_clear,
                self.opt_category,
                self.opt_supplier,
                self.opt_status,
                self.opt_sort_col,
                self.opt_sort_dir,
            ],
            on_submit=self.apply_filters,
        )

        # Result count & active filter banner
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
        header_frame = ctk.CTkFrame(self.table_container, fg_color=COLOR_TABLE_HEADER, height=36, corner_radius=6)
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

    def _on_search_key_release(self, event=None) -> None:
        """Debounced live search on key release (200ms) to prevent keystroke flooding."""
        if event and event.keysym in (
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Caps_Lock", "Tab", "Escape",
            "Return", "Up", "Down", "Left", "Right",
        ):
            return
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(200, self.apply_filters)

    def _on_search_enter(self) -> None:
        """Immediate search execution when Enter is pressed."""
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None
        self.apply_filters()

    def _populate_filter_dropdowns(self) -> None:
        """Dynamically populate category and supplier dropdowns only when values changed."""
        try:
            cats = ["All Categories"] + get_distinct_categories(custom_path=self.db_path)
            sups = ["All Suppliers"] + get_distinct_suppliers(custom_path=self.db_path)

            if self._cached_categories != cats:
                self._cached_categories = cats
                current_cat = self.opt_category.get()
                self.opt_category.configure(values=cats)
                if current_cat in cats:
                    self.opt_category.set(current_cat)
                else:
                    self.opt_category.set("All Categories")

            if self._cached_suppliers != sups:
                self._cached_suppliers = sups
                current_sup = self.opt_supplier.get()
                self.opt_supplier.configure(values=sups)
                if current_sup in sups:
                    self.opt_supplier.set(current_sup)
                else:
                    self.opt_supplier.set("All Suppliers")
        except Exception as exc:
            logger.exception("Error populating filter dropdowns: %s", exc)

    def apply_filters(self) -> None:
        """Collect current filter inputs and refresh product table."""
        search_query = self.search_entry.get().strip()
        category = self.opt_category.get()
        supplier = self.opt_supplier.get()
        status = self.opt_status.get()
        sort_col = self.opt_sort_col.get()
        sort_dir = self.opt_sort_dir.get()

        criteria = FilterCriteria(
            search_query=search_query if search_query else None,
            category=category if category != "All Categories" else None,
            supplier=supplier if supplier != "All Suppliers" else None,
            stock_status=status if status != "All Statuses" else None,
            sort_by=sort_col,
            sort_direction="ASC" if "asc" in sort_dir.lower() else "DESC",
        )

        self.refresh_products(criteria=criteria)

    def clear_all_filters(self) -> None:
        """Reset all search filters and sorting back to default view."""
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None

        self.search_entry.delete(0, "end")
        self.opt_category.set("All Categories")
        self.opt_supplier.set("All Suppliers")
        self.opt_status.set("All Statuses")
        self.opt_sort_col.set("Last Updated")
        self.opt_sort_dir.set("Descending")
        self.refresh_products(criteria=FilterCriteria())

    def apply_initial_criteria(self, criteria: FilterCriteria) -> None:
        """Pre-populate filter/sort controls from incoming deep-link criteria and query products."""
        self._populate_filter_dropdowns()

        # Pre-fill search query
        self.search_entry.delete(0, "end")
        if criteria.search_query:
            self.search_entry.insert(0, criteria.search_query)

        # Pre-fill category
        cats = self.opt_category.cget("values")
        if criteria.category and criteria.category in cats:
            self.opt_category.set(criteria.category)
        else:
            self.opt_category.set("All Categories")

        # Pre-fill supplier
        sups = self.opt_supplier.cget("values")
        if criteria.supplier and criteria.supplier in sups:
            self.opt_supplier.set(criteria.supplier)
        else:
            self.opt_supplier.set("All Suppliers")

        # Pre-fill status
        valid_statuses = ["All Statuses", "In Stock", "Low Stock", "Out of Stock"]
        if criteria.stock_status and criteria.stock_status in valid_statuses:
            self.opt_status.set(criteria.stock_status)
        else:
            self.opt_status.set("All Statuses")

        # Pre-fill sort column
        sort_col_map = {
            "updated_at": "Last Updated",
            "last updated": "Last Updated",
            "product_id": "Product ID",
            "name": "Product Name",
            "category": "Category",
            "supplier": "Supplier",
            "quantity": "Quantity",
            "price": "Price",
            "stock_status": "Stock Status",
        }
        requested_col = str(criteria.sort_by).strip().lower()
        if requested_col in sort_col_map:
            self.opt_sort_col.set(sort_col_map[requested_col])
        elif criteria.sort_by in self.opt_sort_col.cget("values"):
            self.opt_sort_col.set(criteria.sort_by)
        else:
            self.opt_sort_col.set("Last Updated")

        # Pre-fill sort direction
        if criteria.sort_direction and "asc" in str(criteria.sort_direction).lower():
            self.opt_sort_dir.set("Ascending")
        else:
            self.opt_sort_dir.set("Descending")

        self.refresh_products(criteria=criteria)

    def refresh_products(self, criteria: Optional[FilterCriteria] = None) -> None:
        """Execute filtered query from SQLite and re-render rows with widget recycling (zero flicker)."""
        if criteria is None:
            # Reconstruct from UI values
            self.apply_filters()
            return

        self._populate_filter_dropdowns()

        try:
            self.products = filter_products(criteria, custom_path=self.db_path)
            total_count = len(self.products)

            # Build descriptive status message
            active_filters = []
            if criteria.search_query:
                active_filters.append(f"Search='{criteria.search_query}'")
            if criteria.category and criteria.category != "All Categories":
                active_filters.append(f"Category='{criteria.category}'")
            if criteria.supplier and criteria.supplier != "All Suppliers":
                active_filters.append(f"Supplier='{criteria.supplier}'")
            if criteria.stock_status and criteria.stock_status != "All Statuses":
                active_filters.append(f"Status='{criteria.stock_status}'")
            active_filters.append(f"Sorted by {criteria.sort_by} ({criteria.sort_direction.upper()})")

            filter_desc = " • ".join(active_filters)
            self.count_lbl.configure(text=f"Showing {total_count} product(s) ({filter_desc})")

            if not self.products:
                for row in self._row_pool:
                    row.pack_forget()
                self._show_empty_state()
            else:
                self._hide_empty_state()
                sym = SettingsService.get_currency_symbol(custom_path=self.db_path)
                for idx, prod in enumerate(self.products):
                    if idx < len(self._row_pool):
                        row = self._row_pool[idx]
                        row.update_product(prod, is_alt=(idx % 2 == 1), currency_sym=sym)
                        if row.winfo_manager() != "pack":
                            row.pack(fill="x", pady=2, padx=4)
                    else:
                        row = InventoryTableRow(
                            master=self.table_body,
                            on_view=self._view_details,
                            on_edit=self._edit_product,
                            on_delete=self._confirm_delete,
                        )
                        row.update_product(prod, is_alt=(idx % 2 == 1), currency_sym=sym)
                        row.pack(fill="x", pady=2, padx=4)
                        self._row_pool.append(row)

                # Unmap any excess rows from longer prior queries
                for idx in range(len(self.products), len(self._row_pool)):
                    self._row_pool[idx].pack_forget()

        except Exception as exc:
            logger.exception("Error filtering products.")
            self.count_lbl.configure(text="Error querying database.")

    def _show_empty_state(self) -> None:
        """Display helpful empty state container."""
        if self._empty_box is None:
            self._empty_box = ctk.CTkFrame(self.table_body, fg_color="transparent")
            icon = ctk.CTkLabel(self._empty_box, text="🔍", font=(FONT_BODY[0], 42))
            icon.pack(pady=(10, 4))

            msg = ctk.CTkLabel(
                self._empty_box,
                text="No products match the selected search or filter criteria.",
                font=FONT_SECTION,
                text_color=COLOR_TEXT_PRIMARY,
            )
            msg.pack()

            tip = ctk.CTkLabel(
                self._empty_box,
                text="Try adjusting your filter options or click 'Clear All' to reset.",
                font=FONT_SMALL,
                text_color=COLOR_TEXT_MUTED,
            )
            tip.pack(pady=(4, 16))

            btn = SecondaryButton(self._empty_box, text="Clear All Filters", command=self.clear_all_filters, width=140)
            btn.pack()

        if self._empty_box.winfo_manager() != "pack":
            self._empty_box.pack(expand=True, fill="both", pady=40)

    def _hide_empty_state(self) -> None:
        """Hide empty state container if visible."""
        if self._empty_box is not None and self._empty_box.winfo_manager() == "pack":
            self._empty_box.pack_forget()

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
        ProductDetailsModal(parent=self.winfo_toplevel(), product=product, db_path=self.db_path)

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
        self._cached_categories = None
        self._cached_suppliers = None
        self.refresh_products()
        if self.on_data_changed:
            self.on_data_changed()

    def destroy(self) -> None:
        """Safely cancel pending search timers and clean up pooled rows."""
        if hasattr(self, "_search_after_id") and self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None
        super().destroy()
