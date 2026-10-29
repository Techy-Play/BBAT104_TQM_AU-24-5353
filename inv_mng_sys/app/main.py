"""Main application entry point and GUI window coordinator.

Orchestrates:
1. Database initialization.
2. Startup state routing (Setup vs Login vs Dashboard).
3. Persistent session management.
4. Top-level navigation: Dashboard (Phase 5), Inventory Management (Phase 6), Settings, and Logout.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional
import customtkinter as ctk

# Ensure project root is in sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.authentication.login import logout_user, restore_session
from app.authentication.security import UserSession
from app.authentication.setup import is_first_run
from app.dashboard.dashboard import DashboardFrame
from app.database.schema import init_database
from app.inventory.filters import FilterCriteria
from app.settings.settings import SettingsService
from app.ui.components import CardFrame, DangerButton, SecondaryButton
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_SURFACE_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SECTION,
)
from app.ui.views_auth import FirstRunSetupFrame, LoginFrame
from app.ui.views_inventory import InventoryView
from app.ui.views_settings import SettingsView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ims")


class IMSApplication(ctk.CTk):
    """Main desktop application window managing view transitions and active session."""

    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        self.db_path = db_path
        self.current_session: Optional[UserSession] = None
        self.current_view: Optional[ctk.CTkFrame] = None
        self.views: dict[str, ctk.CTkFrame] = {}
        self.nav_bar: Optional[ctk.CTkFrame] = None
        self.content_container: Optional[ctk.CTkFrame] = None
        self._data_dirty: bool = False

        # Apply persistent theme setting
        saved_theme = SettingsService.get_theme_preference(custom_path=self.db_path)
        ctk.set_appearance_mode(saved_theme)

        # Ensure root background matches surface palette to prevent resize/redraw color flash
        self.configure(fg_color=COLOR_SURFACE_BG)

        # Window configuration
        self.title("Inventory Management System (IMS) — BBAT104 (Q13)")
        self._set_window_icon()

        # Ensure database tables and indexes exist
        init_database(custom_path=self.db_path)

        self._route_initial_view()

    def _set_window_icon(self) -> None:
        """Set application icon if available."""
        try:
            icon_candidates = [
                PROJECT_DIR / "app_icon.ico",
                Path(sys.executable).resolve().parent / "app_icon.ico",
                Path(sys.executable).resolve().parent / "_internal" / "app_icon.ico",
                Path(getattr(sys, "_MEIPASS", "")) / "app_icon.ico" if hasattr(sys, "_MEIPASS") else None,
                Path(__file__).resolve().parent.parent / "app_icon.ico",
            ]
            for candidate in icon_candidates:
                if candidate and Path(candidate).is_file():
                    self.iconbitmap(str(candidate))
                    break
        except Exception:
            pass

    def _resize_and_center(self, width: int, height: int, min_w: int, min_h: int) -> None:
        """Resize and center the application window on screen with constraints."""
        self.target_width = width
        self.target_height = height
        self.minsize(min_w, min_h)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(0, int((screen_w - width) / 2))
        pos_y = max(0, int((screen_h - height) / 2))
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def _clear_all(self) -> None:
        """Clear all active view widgets and cached views from the window."""
        if hasattr(self, "views") and self.views:
            for v in list(self.views.values()):
                try:
                    if v.winfo_exists():
                        v.destroy()
                except Exception:
                    pass
            self.views.clear()
        if self.nav_bar is not None:
            self.nav_bar.destroy()
            self.nav_bar = None
        if self.content_container is not None:
            self.content_container.destroy()
            self.content_container = None
        if self.current_view is not None:
            try:
                if self.current_view.winfo_exists():
                    self.current_view.destroy()
            except Exception:
                pass
            self.current_view = None

    def _route_initial_view(self) -> None:
        """Route to setup, login, or dashboard based on database and session state."""
        if is_first_run(custom_path=self.db_path):
            logger.info("First-run detected: routing to setup wizard.")
            self.show_setup()
            return

        session = restore_session(custom_path=self.db_path)
        if session:
            logger.info("Active session restored for user '%s'.", session.username)
            self.show_app_shell(session)
        else:
            logger.info("No active session: routing to login.")
            self.show_login()

    def show_setup(self, reset_notice: bool = False) -> None:
        """Display the first-run account setup screen in a compact non-scrolling card."""
        self._clear_all()
        self._resize_and_center(680, 520, 620, 480)
        self.current_view = FirstRunSetupFrame(
            master=self,
            on_success=self.show_app_shell,
            reset_notice=reset_notice,
            db_path=self.db_path,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_login(self) -> None:
        """Display the user authentication screen with compact geometry."""
        self._clear_all()
        self._resize_and_center(480, 600, 440, 540)
        self.current_view = LoginFrame(
            master=self,
            on_success=self.show_app_shell,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_app_shell(self, session: UserSession) -> None:
        """Initialize the authenticated application workspace shell with top navigation."""
        self.current_session = session
        self._clear_all()
        self._resize_and_center(1100, 750, 960, 650)

        # Build Navigation Header
        self._build_nav_bar()

        # Build Container for switching views
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)

        # Default to Dashboard
        self.show_dashboard_view()

    def _build_nav_bar(self) -> None:
        """Construct top persistent navigation header bar with responsive layout."""
        self.nav_bar = CardFrame(self, height=58)
        self.nav_bar.pack(fill="x", padx=20, pady=(12, 0))
        self.nav_bar.pack_propagate(False)

        # Left: Brand / Org Identity (truncated safely if extra long)
        left_box = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        left_box.pack(side="left", padx=16)

        org_name = self.current_session.organization_name
        disp_org = org_name if len(org_name) <= 24 else org_name[:22] + "…"

        self.brand_label = ctk.CTkLabel(
            left_box,
            text=f"📦 {disp_org}",
            font=FONT_HEADING,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.brand_label.pack(side="left")

        # Center: Navigation items
        nav_buttons = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        nav_buttons.pack(side="left", padx=(24, 0))

        self.btn_nav_dash = ctk.CTkButton(
            nav_buttons,
            text="📊 Dashboard",
            command=self.show_dashboard_view,
            width=112,
            height=34,
            corner_radius=6,
            font=FONT_BUTTON,
            hover_color=COLOR_SECONDARY_HOVER,
        )
        self.btn_nav_dash.pack(side="left", padx=4)

        self.btn_nav_inv = ctk.CTkButton(
            nav_buttons,
            text="📦 Inventory",
            command=self.show_inventory_view,
            width=112,
            height=34,
            corner_radius=6,
            font=FONT_BUTTON,
            hover_color=COLOR_SECONDARY_HOVER,
        )
        self.btn_nav_inv.pack(side="left", padx=4)

        self.btn_nav_settings = ctk.CTkButton(
            nav_buttons,
            text="⚙️ Settings",
            command=self.show_settings_view,
            width=100,
            height=34,
            corner_radius=6,
            font=FONT_BUTTON,
            hover_color=COLOR_SECONDARY_HOVER,
        )
        self.btn_nav_settings.pack(side="left", padx=4)

        # Right: User identity tag & Logout
        right_box = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        right_box.pack(side="right", padx=16)

        user_name = self.current_session.full_name
        disp_user = user_name if len(user_name) <= 20 else user_name[:18] + "…"

        self.user_tag = ctk.CTkLabel(
            right_box,
            text=f"👤 {disp_user}",
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
        )
        self.user_tag.pack(side="left", padx=(0, 14))

        btn_logout = DangerButton(
            right_box,
            text="Log Out",
            command=self.handle_logout,
            width=85,
        )
        btn_logout.pack(side="right")

    def _update_nav_active(self, active: str) -> None:
        """Visual tab highlight for navigation buttons."""
        buttons = {
            "dash": self.btn_nav_dash,
            "inv": self.btn_nav_inv,
            "settings": self.btn_nav_settings,
        }
        for key, btn in buttons.items():
            if key == active:
                btn.configure(fg_color=COLOR_PRIMARY, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_PRIMARY, hover_color=COLOR_SECONDARY_HOVER)

    def _clear_content_view(self) -> None:
        if self.current_view is not None:
            self.current_view.pack_forget()
            self.current_view = None

    def show_dashboard_view(self) -> None:
        """Display the main dashboard (Phase 5) without flickering."""
        self._update_nav_active("dash")
        if self.current_view and self.current_view != self.views.get("dash"):
            self.current_view.pack_forget()

        is_new = "dash" not in self.views or not self.views["dash"].winfo_exists()
        if is_new:
            self.views["dash"] = DashboardFrame(
                master=self.content_container,
                user_session=self.current_session,
                on_navigate_inventory=self.show_inventory_view,
                on_navigate_settings=self.show_settings_view,
                on_logout=self.handle_logout,
                db_path=self.db_path,
            )

        self.current_view = self.views["dash"]
        self.current_view.pack(fill="both", expand=True)

        if is_new or self._data_dirty:
            self.views["dash"].refresh_dashboard()
            self._data_dirty = False

    def show_inventory_view(self, initial_criteria: Optional[FilterCriteria] = None) -> None:
        """Display the inventory management workspace (Phase 6), optionally with pre-applied filters."""
        self._update_nav_active("inv")
        if self.current_view and self.current_view != self.views.get("inv"):
            self.current_view.pack_forget()

        is_new = "inv" not in self.views or not self.views["inv"].winfo_exists()
        if is_new:
            self.views["inv"] = InventoryView(
                master=self.content_container,
                on_data_changed=self._on_inventory_data_changed,
                db_path=self.db_path,
                initial_criteria=initial_criteria,
            )
        elif initial_criteria is not None:
            self.views["inv"].apply_initial_criteria(initial_criteria)
        elif self._data_dirty:
            self.views["inv"].refresh_products()
            self._data_dirty = False

        self.current_view = self.views["inv"]
        self.current_view.pack(fill="both", expand=True)

    def _on_inventory_data_changed(self) -> None:
        """Signal views to refresh when inventory data is mutated."""
        self._data_dirty = True
        if "dash" in self.views and self.views["dash"].winfo_exists():
            if self.current_view == self.views["dash"]:
                self.views["dash"].refresh_dashboard()
                self._data_dirty = False
        if "inv" in self.views and self.views["inv"].winfo_exists():
            if self.current_view == self.views["inv"]:
                self.views["inv"].refresh_products()
                self._data_dirty = False

    def show_settings_view(self) -> None:
        """Display application settings."""
        self._update_nav_active("settings")
        if self.current_view and self.current_view != self.views.get("settings"):
            self.current_view.pack_forget()

        if "settings" not in self.views or not self.views["settings"].winfo_exists():
            self.views["settings"] = SettingsView(
                master=self.content_container,
                user_session=self.current_session,
                on_profile_updated=self._on_profile_updated,
                on_account_deleted=self.handle_account_deleted,
                db_path=self.db_path,
            )

        self.current_view = self.views["settings"]
        self.current_view.pack(fill="both", expand=True)

    def handle_account_deleted(self) -> None:
        """Handle complete account and database reset by clearing session and routing to setup."""
        logger.info("User account deleted and database reset. Routing to setup wizard.")
        self.current_session = None
        self._clear_all()
        self.show_setup(reset_notice=True)

    def _on_profile_updated(self, updated_session: UserSession) -> None:
        """Update active session attributes across the application."""
        self.current_session = updated_session
        if self.brand_label:
            org = updated_session.organization_name
            disp_org = org if len(org) <= 24 else org[:22] + "…"
            self.brand_label.configure(text=f"📦 {disp_org}")
        if self.user_tag:
            usr = updated_session.full_name
            disp_usr = usr if len(usr) <= 20 else usr[:18] + "…"
            self.user_tag.configure(text=f"👤 {disp_usr}")
        if "dash" in self.views and self.views["dash"].winfo_exists():
            self.views["dash"].user_session = updated_session
            self.views["dash"].refresh_dashboard()
        if "settings" in self.views and self.views["settings"].winfo_exists():
            self.views["settings"].user_session = updated_session

    def handle_logout(self) -> None:
        """Invalidate session and return to login."""
        if self.current_session:
            logout_user(self.current_session.id, custom_path=self.db_path)
            self.current_session = None
        self._clear_all()
        self.show_login()

    # Backward-compatible method
    def show_dashboard(self, session: UserSession) -> None:
        self.show_app_shell(session)


def main() -> int:
    """Bootstrap application and launch CustomTkinter UI."""
    logger.info("Initializing persistent database layer...")
    init_status = init_database()
    logger.info("Database initialized: %s", init_status["database_path"])

    # Load and apply persisted theme (defaults to system / device default)
    saved_theme = SettingsService.get_theme_preference()
    ctk.set_appearance_mode(saved_theme)
    ctk.set_default_color_theme("blue")

    app = IMSApplication()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
