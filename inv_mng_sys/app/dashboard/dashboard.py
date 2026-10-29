"""Functional CustomTkinter Dashboard view.

Fulfills Phase 5 requirements:
- Personalized greeting and organization identity
- Real SQLite aggregate statistics (Total products, Total quantity, Low stock, Out of stock)
- Dashboard Quick-Search bar with instant retrieval
- Inventory overview table with loading and empty states
- Seamless navigation hooks to Inventory Management, Settings, and Logout
"""

from __future__ import annotations

import datetime
import logging
from typing import Callable, List, Optional
import customtkinter as ctk

from app.authentication.security import UserSession
from app.inventory.crud import (
    Product,
    get_all_products,
    get_inventory_statistics,
)
from app.inventory.filters import FilterCriteria
from app.inventory.search import search_products_quick
from app.ui.components import (
    CardFrame,
    PrimaryButton,
    SecondaryButton,
    StatCard,
    StatusBadge,
    setup_form_keyboard_navigation,
)
from app.ui.dialogs_inventory import ProductDetailsModal, ProductFormModal
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_ROW_ALT,
    COLOR_SECONDARY,
    COLOR_SUCCESS,
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
    FONT_TITLE,
)

logger = logging.getLogger(__name__)


def get_greeting() -> str:
    """Return appropriate time-of-day greeting."""
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


class DashboardFrame(ctk.CTkScrollableFrame):
    """Main application dashboard displaying real-time statistics and quick-search."""

    def __init__(
        self,
        master,
        user_session: UserSession,
        on_navigate_inventory: Optional[Callable[..., None]] = None,
        on_navigate_settings: Optional[Callable[[], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
        db_path: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.user_session = user_session
        self.on_navigate_inventory = on_navigate_inventory
        self.on_navigate_settings = on_navigate_settings
        self.on_logout = on_logout
        self.db_path = db_path

        self._build_ui()
        self.refresh_dashboard()

    def _navigate_to_inventory(self, criteria: Optional[FilterCriteria] = None) -> None:
        """Deep-link navigation into Inventory Management with optional pre-applied filters."""
        if self.on_navigate_inventory:
            try:
                self.on_navigate_inventory(criteria)
            except TypeError:
                self.on_navigate_inventory()

    def update_user_session(self, updated_session: UserSession) -> None:
        """Update active session attributes (e.g. after profile edit in Settings)."""
        self.user_session = updated_session
        self.greeting_label.configure(text=f"{get_greeting()}, {self.user_session.full_name}!")
        self.org_label.configure(text=f"📦 {self.user_session.organization_name}")

    def _build_ui(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=15)

        # Welcome Card
        hero_card = CardFrame(content)
        hero_card.pack(fill="x", pady=(0, 16))

        hero_left = ctk.CTkFrame(hero_card, fg_color="transparent")
        hero_left.pack(side="left", padx=20, pady=18)

        self.greeting_label = ctk.CTkLabel(
            hero_left,
            text=f"{get_greeting()}, {self.user_session.full_name}!",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.greeting_label.pack(anchor="w")

        self.org_label = ctk.CTkLabel(
            hero_left,
            text=f"📦 {self.user_session.organization_name} • Offline Mode",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_MUTED,
            wraplength=480,
            justify="left",
        )
        self.org_label.pack(anchor="w", pady=(4, 0))

        hero_right = ctk.CTkFrame(hero_card, fg_color="transparent")
        hero_right.pack(side="right", padx=20, pady=18)

        btn_add_quick = PrimaryButton(
            hero_right,
            text="➕ Add Product",
            command=self._open_add_modal,
            width=130,
        )
        btn_add_quick.pack(side="left", padx=(0, 8))

        btn_view_inv = SecondaryButton(
            hero_right,
            text="View Inventory",
            command=lambda: self._navigate_to_inventory(None),
            width=130,
        )
        btn_view_inv.pack(side="left")

        # 4 Key Metric Stat Cards with Interactive Deep Links
        stats_grid = ctk.CTkFrame(content, fg_color="transparent")
        stats_grid.pack(fill="x", pady=(0, 16))
        stats_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total = StatCard(
            stats_grid,
            title="Total Products",
            value="0",
            icon="📦",
            accent_color=COLOR_PRIMARY,
            link_text="View All Products ↗",
            on_click=lambda: self._navigate_to_inventory(None),
        )
        self.card_total.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.card_qty = StatCard(
            stats_grid,
            title="Total Stock Qty",
            value="0",
            icon="🔢",
            accent_color=COLOR_INFO,
            link_text="Sort by Quantity ↗",
            on_click=lambda: self._navigate_to_inventory(
                FilterCriteria(sort_by="Quantity", sort_direction="DESC")
            ),
        )
        self.card_qty.grid(row=0, column=1, sticky="ew", padx=6)

        self.card_low = StatCard(
            stats_grid,
            title="Low Stock Alerts",
            value="0",
            icon="⚠️",
            accent_color=COLOR_WARNING,
            link_text="View Low Stock ↗",
            on_click=lambda: self._navigate_to_inventory(
                FilterCriteria(stock_status="Low Stock")
            ),
        )
        self.card_low.grid(row=0, column=2, sticky="ew", padx=6)

        self.card_out = StatCard(
            stats_grid,
            title="Out of Stock",
            value="0",
            icon="🚫",
            accent_color=COLOR_DANGER,
            link_text="View Out of Stock ↗",
            on_click=lambda: self._navigate_to_inventory(
                FilterCriteria(stock_status="Out of Stock")
            ),
        )
        self.card_out.grid(row=0, column=3, sticky="ew", padx=(6, 0))

        # Quick Search Bar
        search_card = CardFrame(content)
        search_card.pack(fill="x", pady=(0, 16))

        search_row = ctk.CTkFrame(search_card, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=12)

        search_lbl = ctk.CTkLabel(search_row, text="🔎 Quick-Search:", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY)
        search_lbl.pack(side="left", padx=(0, 12))

        self.quick_search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search inventory by Product ID, Name, Category, or Supplier...",
            height=38,
            corner_radius=8,
            font=FONT_BODY,
        )
        self.quick_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.quick_search_entry.bind("<Return>", lambda e: self._handle_quick_search())

        btn_qsearch = PrimaryButton(search_row, text="Search", command=self._handle_quick_search, width=90)
        btn_qsearch.pack(side="left", padx=(0, 6))

        btn_qclear = SecondaryButton(search_row, text="Reset", command=self._handle_clear_search, width=80)
        btn_qclear.pack(side="left", padx=(0, 6))

        btn_qopen = SecondaryButton(
            search_row,
            text="Open in Inventory ↗",
            command=self._handle_open_in_inventory,
            width=145,
        )
        btn_qopen.pack(side="left")

        # Setup Tab traversal across quick search controls
        setup_form_keyboard_navigation(
            widgets=[self.quick_search_entry, btn_qsearch, btn_qclear, btn_qopen],
            on_submit=self._handle_quick_search,
        )

        # Inventory Table Overview Card
        self.table_card = CardFrame(content)
        self.table_card.pack(fill="both", expand=True, pady=(0, 10))

        table_top = ctk.CTkFrame(self.table_card, fg_color="transparent")
        table_top.pack(fill="x", padx=16, pady=(16, 8))

        self.table_title = ctk.CTkLabel(
            table_top,
            text="Recent Inventory Overview",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.table_title.pack(side="left")

        btn_refresh = SecondaryButton(table_top, text="🔄 Refresh", command=self.refresh_dashboard, width=90)
        btn_refresh.pack(side="right")

        btn_view_full = SecondaryButton(
            table_top,
            text="View Full Inventory ↗",
            command=lambda: self._navigate_to_inventory(None),
            width=150,
        )
        btn_view_full.pack(side="right", padx=(0, 8))

        # Table Header
        self._build_table_header()

        # Table Items Container
        self.table_body = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.table_body.pack(fill="both", expand=True, padx=8, pady=(0, 16))

    def _build_table_header(self) -> None:
        header_frame = ctk.CTkFrame(self.table_card, fg_color=COLOR_TABLE_HEADER, height=36, corner_radius=6)
        header_frame.pack(fill="x", padx=16, pady=(0, 4))
        header_frame.pack_propagate(False)

        cols = [
            ("SKU / ID", 100),
            ("Product Name", 200),
            ("Category", 120),
            ("Supplier", 130),
            ("Quantity", 70),
            ("Price", 75),
            ("Status", 105),
            ("Actions", 130),
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

    def refresh_dashboard(self) -> None:
        """Fetch real statistics and refresh the overview list."""
        try:
            stats = get_inventory_statistics(custom_path=self.db_path)
            self.card_total.update_value(f"{stats['total_products']:,}")
            self.card_qty.update_value(f"{stats['total_quantity']:,}")
            self.card_low.update_value(f"{stats['low_stock_count']:,}")
            self.card_out.update_value(f"{stats['out_of_stock_count']:,}")

            query = self.quick_search_entry.get().strip()
            self._render_table(query if query else None)
        except Exception as exc:
            logger.exception("Error updating dashboard statistics.")

    def _handle_quick_search(self) -> None:
        query = self.quick_search_entry.get().strip()
        self._render_table(query if query else None)

    def _handle_clear_search(self) -> None:
        self.quick_search_entry.delete(0, "end")
        self._render_table(None)

    def _handle_open_in_inventory(self) -> None:
        """Deep-link to Inventory workspace filtered by current Quick-Search query."""
        query = self.quick_search_entry.get().strip()
        criteria = FilterCriteria(search_query=query) if query else None
        self._navigate_to_inventory(criteria)

    def _render_table(self, query: Optional[str] = None) -> None:
        # Detach table frame during update to batch rendering and eliminate redraw flicker
        self.table_body.pack_forget()
        try:
            for child in self.table_body.winfo_children():
                child.destroy()

            if query:
                prods = search_products_quick(query, custom_path=self.db_path)
                self.table_title.configure(text=f"Quick-Search Results for '{query}' ({len(prods)} found)")
            else:
                prods = get_all_products(custom_path=self.db_path)[:15]  # Latest 15 records for dashboard
                self.table_title.configure(text="Recent Inventory Records (Top 15)")

            if not prods:
                empty_box = ctk.CTkFrame(self.table_body, fg_color="transparent")
                empty_box.pack(fill="both", expand=True, pady=30)
                ctk.CTkLabel(empty_box, text="📦", font=(FONT_BODY[0], 36)).pack()
                ctk.CTkLabel(
                    empty_box,
                    text="No inventory products found." if not query else f"No products matching '{query}'.",
                    font=FONT_BODY,
                    text_color=COLOR_TEXT_MUTED,
                ).pack(pady=4)
                return

            for idx, prod in enumerate(prods):
                bg_col = COLOR_ROW_ALT if (idx % 2 == 1) else "transparent"
                row = ctk.CTkFrame(self.table_body, fg_color=bg_col, corner_radius=6, height=40)
                row.pack(fill="x", pady=2, padx=4)
                row.pack_propagate(False)

                ctk.CTkLabel(row, text=prod.product_id, font=FONT_BODY, width=100, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(row, text=prod.name, font=FONT_BODY, width=200, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(row, text=prod.category, font=FONT_BODY, width=120, anchor="w", text_color=COLOR_TEXT_MUTED).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=prod.supplier, font=FONT_BODY, width=130, anchor="w", text_color=COLOR_TEXT_MUTED).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=str(prod.quantity), font=FONT_BODY, width=70, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(row, text=f"${prod.price:.2f}", font=FONT_BODY, width=75, anchor="w").pack(side="left", padx=4)

                status_box = ctk.CTkFrame(row, fg_color="transparent", width=105)
                status_box.pack(side="left", padx=4)
                status_box.pack_propagate(False)
                badge = StatusBadge(status_box, status=prod.stock_status)
                badge.pack(side="left", pady=6)

                act_box = ctk.CTkFrame(row, fg_color="transparent", width=130)
                act_box.pack(side="left", padx=4)
                act_box.pack_propagate(False)

                btn_view = SecondaryButton(
                    act_box,
                    text="View",
                    width=54,
                    height=28,
                    command=lambda p=prod: ProductDetailsModal(parent=self.winfo_toplevel(), product=p),
                )
                btn_view.pack(side="left", padx=(0, 4), pady=6)

                btn_open = PrimaryButton(
                    act_box,
                    text="Open ↗",
                    width=62,
                    height=28,
                    command=lambda p=prod: self._navigate_to_inventory(FilterCriteria(search_query=p.product_id)),
                )
                btn_open.pack(side="left", pady=6)

        except Exception as exc:
            logger.exception("Error rendering dashboard table.")
        finally:
            self.table_body.pack(fill="both", expand=True, padx=8, pady=(0, 16))

    def _open_add_modal(self) -> None:
        ProductFormModal(
            parent=self.winfo_toplevel(),
            on_success=lambda _p: self.refresh_dashboard(),
            product=None,
            db_path=self.db_path,
        )


# Backward-compatible alias for any legacy imports
DashboardPlaceholderFrame = DashboardFrame
