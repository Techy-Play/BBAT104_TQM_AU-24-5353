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
    get_product_by_id,
    get_shop_owner_analysis,
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
    FONT_BODY_BOLD,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_TABLE_HEADER,
    FONT_TITLE,
)

logger = logging.getLogger(__name__)


class CategoryAnalysisRow(ctk.CTkFrame):
    """Row displaying category inventory capital allocation and percentage share."""

    def __init__(self, master, on_filter: Callable[[str], None]):
        super().__init__(master, fg_color=COLOR_SECONDARY, corner_radius=6, height=38)
        self.pack_propagate(False)
        self._on_filter = on_filter
        self.category_name = ""

        self.name_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY_BOLD, width=120, anchor="w", text_color=COLOR_TEXT_PRIMARY)
        self.name_lbl.pack(side="left", padx=(10, 4))

        self.units_lbl = ctk.CTkLabel(self, text="", font=FONT_SMALL, width=80, anchor="w", text_color=COLOR_TEXT_MUTED)
        self.units_lbl.pack(side="left", padx=4)

        self.val_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY_BOLD, width=90, anchor="e", text_color=COLOR_SUCCESS)
        self.val_lbl.pack(side="left", padx=4)

        self.pct_lbl = ctk.CTkLabel(self, text="", font=FONT_SMALL, width=50, anchor="e", text_color=COLOR_TEXT_MUTED)
        self.pct_lbl.pack(side="left", padx=4)

        self.progress = ctk.CTkProgressBar(self, width=80, height=8, progress_color=COLOR_PRIMARY)
        self.progress.pack(side="left", padx=(6, 8))

        self.btn_filter = SecondaryButton(self, text="Filter ↗", width=62, height=26, command=self._handle_click)
        self.btn_filter.pack(side="right", padx=(4, 8))

    def _handle_click(self) -> None:
        if self.category_name and self._on_filter:
            self._on_filter(self.category_name)

    def update_data(self, cat_data: dict) -> None:
        self.category_name = cat_data["category"]
        self.name_lbl.configure(text=cat_data["category"])
        self.units_lbl.configure(text=f"{cat_data['units']} units")
        self.val_lbl.configure(text=f"${cat_data['value']:,.2f}")
        self.pct_lbl.configure(text=f"{cat_data['percent_share']}%")
        self.progress.set(min(1.0, max(0.0, cat_data["percent_share"] / 100.0)))


class RestockUrgencyRow(ctk.CTkFrame):
    """Row displaying actionable replenishment alert for items at or below custom threshold."""

    def __init__(self, master, on_view: Callable[[int], None], on_open: Callable[[str], None]):
        super().__init__(master, fg_color=COLOR_SECONDARY, corner_radius=6, height=38)
        self.pack_propagate(False)
        self._on_view = on_view
        self._on_open = on_open
        self.item_id: Optional[int] = None
        self.sku: str = ""

        self.badge_urgency = ctk.CTkLabel(
            self,
            text="",
            font=FONT_SMALL,
            corner_radius=4,
            width=50,
            text_color="#ffffff",
            fg_color=COLOR_DANGER,
        )
        self.badge_urgency.pack(side="left", padx=(8, 4), pady=6)

        self.name_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY_BOLD, width=160, anchor="w", text_color=COLOR_TEXT_PRIMARY)
        self.name_lbl.pack(side="left", padx=4)

        self.qty_lbl = ctk.CTkLabel(self, text="", font=FONT_SMALL, width=120, anchor="w", text_color=COLOR_TEXT_MUTED)
        self.qty_lbl.pack(side="left", padx=4)

        self.deficit_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY_BOLD, width=70, anchor="e", text_color=COLOR_WARNING)
        self.deficit_lbl.pack(side="left", padx=4)

        self.btn_open = PrimaryButton(self, text="Open ↗", width=62, height=26, command=self._handle_open)
        self.btn_open.pack(side="right", padx=(4, 8))

        self.btn_view = SecondaryButton(self, text="View", width=52, height=26, command=self._handle_view)
        self.btn_view.pack(side="right", padx=(0, 4))

    def _handle_view(self) -> None:
        if self.item_id and self._on_view:
            self._on_view(self.item_id)

    def _handle_open(self) -> None:
        if self.sku and self._on_open:
            self._on_open(self.sku)

    def update_data(self, item_data: dict) -> None:
        self.item_id = item_data["id"]
        self.sku = item_data["product_id"]
        urgency = item_data.get("urgency", "WARNING")
        if urgency == "CRITICAL":
            self.badge_urgency.configure(text="OUT", fg_color=COLOR_DANGER)
        elif urgency == "HIGH":
            self.badge_urgency.configure(text="CRIT", fg_color=COLOR_WARNING)
        else:
            self.badge_urgency.configure(text="LOW", fg_color=COLOR_INFO)

        self.name_lbl.configure(text=f"{item_data['name']} ({item_data['product_id']})")
        self.qty_lbl.configure(text=f"Qty: {item_data['quantity']} / Thresh: {item_data['threshold']}")
        shortage = item_data.get("shortage", 0)
        self.deficit_lbl.configure(text=f"-{shortage} units" if shortage > 0 else "0 units")


class DashboardTableRow(ctk.CTkFrame):
    """Pooled dashboard table row reused across refreshes to eliminate redraw flicker."""

    def __init__(
        self,
        master,
        on_view: Callable[[Product], None],
        on_open: Callable[[Product], None],
    ):
        super().__init__(master, corner_radius=6, height=40)
        self.pack_propagate(False)
        self._on_view = on_view
        self._on_open = on_open
        self.product: Optional[Product] = None

        self.sku_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=100, anchor="w")
        self.sku_lbl.pack(side="left", padx=4)

        self.name_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=200, anchor="w")
        self.name_lbl.pack(side="left", padx=4)

        self.cat_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=120, anchor="w", text_color=COLOR_TEXT_MUTED)
        self.cat_lbl.pack(side="left", padx=4)

        self.sup_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=130, anchor="w", text_color=COLOR_TEXT_MUTED)
        self.sup_lbl.pack(side="left", padx=4)

        self.qty_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=70, anchor="w")
        self.qty_lbl.pack(side="left", padx=4)

        self.price_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY, width=75, anchor="w")
        self.price_lbl.pack(side="left", padx=4)

        status_box = ctk.CTkFrame(self, fg_color="transparent", width=105)
        status_box.pack(side="left", padx=4)
        status_box.pack_propagate(False)
        self.badge = StatusBadge(status_box, status="In Stock")
        self.badge.pack(side="left", pady=6)

        act_box = ctk.CTkFrame(self, fg_color="transparent", width=130)
        act_box.pack(side="left", padx=4)
        act_box.pack_propagate(False)

        self.btn_view = SecondaryButton(
            act_box,
            text="View",
            width=54,
            height=28,
            command=self._handle_view,
        )
        self.btn_view.pack(side="left", padx=(0, 4), pady=6)

        self.btn_open = PrimaryButton(
            act_box,
            text="Open ↗",
            width=62,
            height=28,
            command=self._handle_open,
        )
        self.btn_open.pack(side="left", pady=6)

    def _handle_view(self) -> None:
        if self.product:
            self._on_view(self.product)

    def _handle_open(self) -> None:
        if self.product:
            self._on_open(self.product)

    def update_product(self, prod: Product, is_alt: bool) -> None:
        """Update row contents in-place without widget reconstruction."""
        self.product = prod
        bg_col = COLOR_ROW_ALT if is_alt else "transparent"
        self.configure(fg_color=bg_col)
        self.sku_lbl.configure(text=prod.product_id)
        self.name_lbl.configure(text=prod.name)
        self.cat_lbl.configure(text=prod.category)
        self.sup_lbl.configure(text=prod.supplier)
        self.qty_lbl.configure(text=str(prod.quantity))
        self.price_lbl.configure(text=f"${prod.price:.2f}")
        self.badge.update_status(prod.stock_status)


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
        self._row_pool: list[DashboardTableRow] = []
        self._category_row_pool: list[CategoryAnalysisRow] = []
        self._restock_row_pool: list[RestockUrgencyRow] = []
        self._empty_box: Optional[ctk.CTkFrame] = None
        self._quick_search_after_id: Optional[str] = None

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

        # 5 Key Metric Stat Cards with Interactive Deep Links
        stats_grid = ctk.CTkFrame(content, fg_color="transparent")
        stats_grid.pack(fill="x", pady=(0, 16))
        stats_grid.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.card_total = StatCard(
            stats_grid,
            title="Total Products",
            value="0",
            icon="📦",
            accent_color=COLOR_PRIMARY,
            link_text="View All Products ↗",
            on_click=lambda: self._navigate_to_inventory(None),
        )
        self.card_total.grid(row=0, column=0, sticky="ew", padx=(0, 4))

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
        self.card_qty.grid(row=0, column=1, sticky="ew", padx=4)

        self.card_val = StatCard(
            stats_grid,
            title="Total Stock Value",
            value="$0.00",
            icon="💰",
            accent_color=COLOR_SUCCESS,
            link_text="Sort by Price ↗",
            on_click=lambda: self._navigate_to_inventory(
                FilterCriteria(sort_by="Price", sort_direction="DESC")
            ),
        )
        self.card_val.grid(row=0, column=2, sticky="ew", padx=4)

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
        self.card_low.grid(row=0, column=3, sticky="ew", padx=4)

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
        self.card_out.grid(row=0, column=4, sticky="ew", padx=(4, 0))

        # Store Inventory & Capital Analytics Card (Shop Owner Dashboard)
        self.analysis_card = CardFrame(content)
        self.analysis_card.pack(fill="x", pady=(0, 16))

        analysis_header = ctk.CTkFrame(self.analysis_card, fg_color="transparent")
        analysis_header.pack(fill="x", padx=16, pady=(16, 8))

        analysis_title_box = ctk.CTkFrame(analysis_header, fg_color="transparent")
        analysis_title_box.pack(side="left")

        ctk.CTkLabel(
            analysis_title_box,
            text="📊 Store Inventory & Capital Analysis",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            analysis_title_box,
            text="Real-time capital distribution, category investment share, and replenishment urgency",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w")

        self.analysis_kpi_lbl = ctk.CTkLabel(
            analysis_header,
            text="Avg SKU: $0.00  •  Avg Unit Price: $0.00",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.analysis_kpi_lbl.pack(side="right")

        # Two-Column Analysis Container
        analysis_cols = ctk.CTkFrame(self.analysis_card, fg_color="transparent")
        analysis_cols.pack(fill="x", padx=16, pady=(0, 16))
        analysis_cols.grid_columnconfigure((0, 1), weight=1, uniform="analysis_cols")

        # LEFT COLUMN: Stock Health & Category Capital Breakdown
        left_col = ctk.CTkFrame(analysis_cols, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Stock Health Pills
        ctk.CTkLabel(
            left_col,
            text="Stock Health & Portfolio Distribution",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        health_box = ctk.CTkFrame(left_col, fg_color=COLOR_SECONDARY, corner_radius=6)
        health_box.pack(fill="x", pady=(0, 12))

        health_row = ctk.CTkFrame(health_box, fg_color="transparent")
        health_row.pack(fill="x", padx=12, pady=10)

        self.health_in_lbl = ctk.CTkLabel(
            health_row,
            text="🟢 In Stock: 0 (0%)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_SUCCESS,
            anchor="w",
        )
        self.health_in_lbl.pack(side="left", expand=True)

        self.health_low_lbl = ctk.CTkLabel(
            health_row,
            text="🟠 Low Stock: 0 (0%)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_WARNING,
            anchor="w",
        )
        self.health_low_lbl.pack(side="left", expand=True)

        self.health_out_lbl = ctk.CTkLabel(
            health_row,
            text="🔴 Out of Stock: 0 (0%)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_DANGER,
            anchor="w",
        )
        self.health_out_lbl.pack(side="left", expand=True)

        # Category Allocation Title & Container
        cat_head_row = ctk.CTkFrame(left_col, fg_color="transparent")
        cat_head_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            cat_head_row,
            text="Top Categories by Capital Allocation",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        self.category_container = ctk.CTkFrame(left_col, fg_color="transparent")
        self.category_container.pack(fill="x")

        self._category_empty_lbl = ctk.CTkLabel(
            self.category_container,
            text="No category data available.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )

        # RIGHT COLUMN: Restock Priority & Replenishment Alerts
        right_col = ctk.CTkFrame(analysis_cols, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        urgency_head_row = ctk.CTkFrame(right_col, fg_color="transparent")
        urgency_head_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            urgency_head_row,
            text="⚠️ Restock Priority (Custom Threshold Alerts)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        self.restock_container = ctk.CTkFrame(right_col, fg_color="transparent")
        self.restock_container.pack(fill="x")

        self._restock_empty_lbl = ctk.CTkLabel(
            self.restock_container,
            text="✅ All product lines healthy! No items at or below threshold.",
            font=FONT_SMALL,
            text_color=COLOR_SUCCESS,
        )

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
        self.quick_search_entry.bind("<KeyRelease>", self._on_quick_search_key_release)
        self.quick_search_entry.bind("<Return>", lambda e: self._on_quick_search_enter())

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
        """Fetch real statistics and refresh the overview list and analysis cards."""
        try:
            stats = get_inventory_statistics(custom_path=self.db_path)
            self.card_total.update_value(f"{stats['total_products']:,}")
            self.card_qty.update_value(f"{stats['total_quantity']:,}")
            self.card_val.update_value(f"${stats['total_value']:,.2f}")
            self.card_low.update_value(f"{stats['low_stock_count']:,}")
            self.card_out.update_value(f"{stats['out_of_stock_count']:,}")

            # Update Shop Owner Analysis
            analysis = get_shop_owner_analysis(custom_path=self.db_path)
            self._update_analysis_section(analysis)

            query = self.quick_search_entry.get().strip()
            self._render_table(query if query else None)
        except Exception as exc:
            logger.exception("Error updating dashboard statistics.")

    def _update_analysis_section(self, analysis: dict) -> None:
        """Update shop owner analysis cards with fresh statistics without UI flicker."""
        try:
            # Header KPIs
            self.analysis_kpi_lbl.configure(
                text=f"Avg SKU: ${analysis['avg_sku_value']:,.2f}  •  Avg Unit: ${analysis['avg_unit_price']:,.2f}"
            )

            # Stock Health
            self.health_in_lbl.configure(
                text=f"🟢 In Stock: {analysis['in_stock_count']:,} ({analysis['in_stock_pct']}%)"
            )
            self.health_low_lbl.configure(
                text=f"🟠 Low Stock: {analysis['low_stock_count']:,} ({analysis['low_stock_pct']}%)"
            )
            self.health_out_lbl.configure(
                text=f"🔴 Out of Stock: {analysis['out_of_stock_count']:,} ({analysis['out_stock_pct']}%)"
            )

            # Categories (Top 5)
            categories = analysis.get("categories", [])[:5]
            if not categories:
                for row in self._category_row_pool:
                    row.pack_forget()
                if self._category_empty_lbl.winfo_manager() != "pack":
                    self._category_empty_lbl.pack(fill="x", pady=10)
            else:
                if self._category_empty_lbl.winfo_manager() == "pack":
                    self._category_empty_lbl.pack_forget()
                for idx, cat_data in enumerate(categories):
                    if idx < len(self._category_row_pool):
                        row = self._category_row_pool[idx]
                        row.update_data(cat_data)
                        if row.winfo_manager() != "pack":
                            row.pack(fill="x", pady=2)
                    else:
                        row = CategoryAnalysisRow(
                            master=self.category_container,
                            on_filter=lambda cat: self._navigate_to_inventory(FilterCriteria(category=cat)),
                        )
                        row.update_data(cat_data)
                        row.pack(fill="x", pady=2)
                        self._category_row_pool.append(row)

                # Unmap extra rows
                for idx in range(len(categories), len(self._category_row_pool)):
                    self._category_row_pool[idx].pack_forget()

            # Restock Urgency (Top 5)
            restock_items = analysis.get("restock_alerts", [])[:5]
            if not restock_items:
                for row in self._restock_row_pool:
                    row.pack_forget()
                if self._restock_empty_lbl.winfo_manager() != "pack":
                    self._restock_empty_lbl.pack(fill="x", pady=10)
            else:
                if self._restock_empty_lbl.winfo_manager() == "pack":
                    self._restock_empty_lbl.pack_forget()
                for idx, item_data in enumerate(restock_items):
                    if idx < len(self._restock_row_pool):
                        row = self._restock_row_pool[idx]
                        row.update_data(item_data)
                        if row.winfo_manager() != "pack":
                            row.pack(fill="x", pady=2)
                    else:
                        row = RestockUrgencyRow(
                            master=self.restock_container,
                            on_view=self._open_product_details_by_id,
                            on_open=lambda sku: self._navigate_to_inventory(FilterCriteria(search_query=sku)),
                        )
                        row.update_data(item_data)
                        row.pack(fill="x", pady=2)
                        self._restock_row_pool.append(row)

                # Unmap extra rows
                for idx in range(len(restock_items), len(self._restock_row_pool)):
                    self._restock_row_pool[idx].pack_forget()

        except Exception as exc:
            logger.exception("Error updating shop owner analysis section.")

    def _open_product_details_by_id(self, item_id: int) -> None:
        """Open ProductDetailsModal for a given product ID."""
        prod = get_product_by_id(item_id, custom_path=self.db_path)
        if prod:
            ProductDetailsModal(parent=self.winfo_toplevel(), product=prod)

    def _on_quick_search_key_release(self, event=None) -> None:
        """Debounced live search on key release (200ms) to avoid keystroke flooding."""
        if event and event.keysym in (
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Caps_Lock", "Tab", "Escape",
            "Return", "Up", "Down", "Left", "Right",
        ):
            return
        if self._quick_search_after_id:
            try:
                self.after_cancel(self._quick_search_after_id)
            except Exception:
                pass
        self._quick_search_after_id = self.after(200, self._handle_quick_search)

    def _on_quick_search_enter(self) -> None:
        """Immediate search execution when Enter is pressed."""
        if self._quick_search_after_id:
            try:
                self.after_cancel(self._quick_search_after_id)
            except Exception:
                pass
            self._quick_search_after_id = None
        self._handle_quick_search()

    def _handle_quick_search(self) -> None:
        query = self.quick_search_entry.get().strip()
        self._render_table(query if query else None)

    def _handle_clear_search(self) -> None:
        if self._quick_search_after_id:
            try:
                self.after_cancel(self._quick_search_after_id)
            except Exception:
                pass
            self._quick_search_after_id = None
        self.quick_search_entry.delete(0, "end")
        self._render_table(None)

    def _handle_open_in_inventory(self) -> None:
        """Deep-link to Inventory workspace filtered by current Quick-Search query."""
        query = self.quick_search_entry.get().strip()
        criteria = FilterCriteria(search_query=query) if query else None
        self._navigate_to_inventory(criteria)

    def _render_table(self, query: Optional[str] = None) -> None:
        """Render recent/search inventory records using row widget recycling (zero redraw flicker)."""
        try:
            if query:
                prods = search_products_quick(query, custom_path=self.db_path)
                self.table_title.configure(text=f"Quick-Search Results for '{query}' ({len(prods)} found)")
            else:
                prods = get_all_products(custom_path=self.db_path)[:15]  # Latest 15 records for dashboard
                self.table_title.configure(text="Recent Inventory Records (Top 15)")

            if not prods:
                for row in self._row_pool:
                    row.pack_forget()
                self._show_empty_state(query)
            else:
                self._hide_empty_state()
                for idx, prod in enumerate(prods):
                    if idx < len(self._row_pool):
                        row = self._row_pool[idx]
                        row.update_product(prod, is_alt=(idx % 2 == 1))
                        if row.winfo_manager() != "pack":
                            row.pack(fill="x", pady=2, padx=4)
                    else:
                        row = DashboardTableRow(
                            master=self.table_body,
                            on_view=lambda p: ProductDetailsModal(parent=self.winfo_toplevel(), product=p),
                            on_open=lambda p: self._navigate_to_inventory(FilterCriteria(search_query=p.product_id)),
                        )
                        row.update_product(prod, is_alt=(idx % 2 == 1))
                        row.pack(fill="x", pady=2, padx=4)
                        self._row_pool.append(row)

                # Unmap any excess rows
                for idx in range(len(prods), len(self._row_pool)):
                    self._row_pool[idx].pack_forget()

        except Exception as exc:
            logger.exception("Error rendering dashboard table.")

    def _show_empty_state(self, query: Optional[str] = None) -> None:
        """Display helpful empty state container."""
        if self._empty_box is None:
            self._empty_box = ctk.CTkFrame(self.table_body, fg_color="transparent")
            ctk.CTkLabel(self._empty_box, text="📦", font=(FONT_BODY[0], 36)).pack()
            self._empty_lbl = ctk.CTkLabel(
                self._empty_box,
                text="",
                font=FONT_BODY,
                text_color=COLOR_TEXT_MUTED,
            )
            self._empty_lbl.pack(pady=4)

        msg = "No inventory products found." if not query else f"No products matching '{query}'."
        self._empty_lbl.configure(text=msg)
        if self._empty_box.winfo_manager() != "pack":
            self._empty_box.pack(fill="both", expand=True, pady=30)

    def _hide_empty_state(self) -> None:
        """Hide empty state container if visible."""
        if self._empty_box is not None and self._empty_box.winfo_manager() == "pack":
            self._empty_box.pack_forget()

    def _open_add_modal(self) -> None:
        ProductFormModal(
            parent=self.winfo_toplevel(),
            on_success=lambda _p: self.refresh_dashboard(),
            product=None,
            db_path=self.db_path,
        )

    def destroy(self) -> None:
        """Safely cancel pending search timers."""
        if hasattr(self, "_quick_search_after_id") and self._quick_search_after_id:
            try:
                self.after_cancel(self._quick_search_after_id)
            except Exception:
                pass
            self._quick_search_after_id = None
        super().destroy()


# Backward-compatible alias for any legacy imports
DashboardPlaceholderFrame = DashboardFrame
