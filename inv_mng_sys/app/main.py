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
from app.ui.components import CardFrame, DangerButton, SecondaryButton
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
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
        self.nav_bar: Optional[ctk.CTkFrame] = None
        self.content_container: Optional[ctk.CTkFrame] = None

        # Window configuration
        self.title("Inventory Management System (IMS) — BBAT104 (Q13)")
        self.geometry("1080x750")
        self.minsize(920, 650)

        # Center window on screen
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(0, int((screen_w - 1080) / 2))
        pos_y = max(0, int((screen_h - 750) / 2))
        self.geometry(f"1080x750+{pos_x}+{pos_y}")

        # Ensure database tables and indexes exist
        init_database(custom_path=self.db_path)

        self._route_initial_view()

    def _clear_all(self) -> None:
        """Clear all active view widgets from the window."""
        if self.nav_bar is not None:
            self.nav_bar.destroy()
            self.nav_bar = None
        if self.content_container is not None:
            self.content_container.destroy()
            self.content_container = None
        if self.current_view is not None:
            self.current_view.destroy()
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

    def show_setup(self) -> None:
        """Display the first-run account setup screen."""
        self._clear_all()
        self.current_view = FirstRunSetupFrame(
            master=self,
            on_success=self.show_app_shell,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_login(self) -> None:
        """Display the user authentication screen."""
        self._clear_all()
        self.current_view = LoginFrame(
            master=self,
            on_success=self.show_app_shell,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_app_shell(self, session: UserSession) -> None:
        """Initialize the authenticated application workspace shell with top navigation."""
        self.current_session = session
        self._clear_all()

        # Build Navigation Header
        self._build_nav_bar()

        # Build Container for switching views
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)

        # Default to Dashboard
        self.show_dashboard_view()

    def _build_nav_bar(self) -> None:
        """Construct top persistent navigation header bar."""
        self.nav_bar = CardFrame(self, height=64)
        self.nav_bar.pack(fill="x", padx=20, pady=(15, 0))
        self.nav_bar.pack_propagate(False)

        # Left: Brand / Org Identity
        left_box = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        left_box.pack(side="left", padx=16)

        self.brand_label = ctk.CTkLabel(
            left_box,
            text=f"📦 {self.current_session.organization_name}",
            font=FONT_HEADING,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.brand_label.pack(side="left")

        # Center: Navigation items
        nav_buttons = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        nav_buttons.pack(side="left", padx=(30, 0))

        self.btn_nav_dash = ctk.CTkButton(
            nav_buttons,
            text="📊 Dashboard",
            command=self.show_dashboard_view,
            width=110,
            height=34,
            corner_radius=6,
            font=FONT_BUTTON,
        )
        self.btn_nav_dash.pack(side="left", padx=4)

        self.btn_nav_inv = ctk.CTkButton(
            nav_buttons,
            text="📦 Inventory",
            command=self.show_inventory_view,
            width=110,
            height=34,
            corner_radius=6,
            font=FONT_BUTTON,
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
        )
        self.btn_nav_settings.pack(side="left", padx=4)

        # Right: User identity tag & Logout
        right_box = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        right_box.pack(side="right", padx=16)

        self.user_tag = ctk.CTkLabel(
            right_box,
            text=f"👤 {self.current_session.full_name}",
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
        )
        self.user_tag.pack(side="left", padx=(0, 16))

        btn_logout = DangerButton(
            right_box,
            text="Log Out",
            command=self.handle_logout,
            width=90,
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
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_PRIMARY)

    def _clear_content_view(self) -> None:
        if self.current_view is not None:
            self.current_view.destroy()
            self.current_view = None

    def show_dashboard_view(self) -> None:
        """Display the main dashboard (Phase 5)."""
        self._update_nav_active("dash")
        self._clear_content_view()
        self.current_view = DashboardFrame(
            master=self.content_container,
            user_session=self.current_session,
            on_navigate_inventory=self.show_inventory_view,
            on_navigate_settings=self.show_settings_view,
            on_logout=self.handle_logout,
            db_path=self.db_path,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_inventory_view(self) -> None:
        """Display the inventory management workspace (Phase 6)."""
        self._update_nav_active("inv")
        self._clear_content_view()
        self.current_view = InventoryView(
            master=self.content_container,
            on_data_changed=lambda: None,
            db_path=self.db_path,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_settings_view(self) -> None:
        """Display application settings."""
        self._update_nav_active("settings")
        self._clear_content_view()
        self.current_view = SettingsView(
            master=self.content_container,
            user_session=self.current_session,
            on_profile_updated=self._on_profile_updated,
        )
        self.current_view.pack(fill="both", expand=True)

    def _on_profile_updated(self, updated_session: UserSession) -> None:
        """Update active session attributes across the application."""
        self.current_session = updated_session
        if self.brand_label:
            self.brand_label.configure(text=f"📦 {updated_session.organization_name}")
        if self.user_tag:
            self.user_tag.configure(text=f"👤 {updated_session.full_name}")

    def handle_logout(self) -> None:
        """Invalidate session and return to login."""
        if self.current_session:
            logout_user(self.current_session.id, custom_path=self.db_path)
            self.current_session = None
        self.show_login()

    # Backward-compatible method
    def show_dashboard(self, session: UserSession) -> None:
        self.show_app_shell(session)


def main() -> int:
    """Bootstrap application and launch CustomTkinter UI."""
    logger.info("Initializing persistent database layer...")
    init_status = init_database()
    logger.info("Database initialized: %s", init_status["database_path"])

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = IMSApplication()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
