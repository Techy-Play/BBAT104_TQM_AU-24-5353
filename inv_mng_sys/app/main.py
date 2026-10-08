"""Main application entry point and GUI window coordinator.

Orchestrates:
1. Database initialization (idempotent, persistent).
2. Startup state resolution:
   - No user exists -> FirstRunSetupFrame
   - User exists with active session -> DashboardPlaceholderFrame
   - User exists without active session -> LoginFrame
3. Session lifecycle (login, restore, logout).
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
from app.dashboard.dashboard import DashboardPlaceholderFrame
from app.database.schema import init_database
from app.ui.views_auth import FirstRunSetupFrame, LoginFrame

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

        # Window configuration
        self.title("Inventory Management System (IMS) — BBAT104 (Q13)")
        self.geometry("980x700")
        self.minsize(860, 620)

        # Center window on screen
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(0, int((screen_w - 980) / 2))
        pos_y = max(0, int((screen_h - 700) / 2))
        self.geometry(f"980x700+{pos_x}+{pos_y}")

        self._route_initial_view()

    def _clear_view(self) -> None:
        """Destroy current view widget to prevent memory leak and redraw cleanly."""
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
            self.show_dashboard(session)
        else:
            logger.info("No active session: routing to login.")
            self.show_login()

    def show_setup(self) -> None:
        """Display the first-run account setup screen."""
        self._clear_view()
        self.current_view = FirstRunSetupFrame(
            master=self,
            on_success=self.show_dashboard,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_login(self) -> None:
        """Display the user authentication screen."""
        self._clear_view()
        self.current_view = LoginFrame(
            master=self,
            on_success=self.show_dashboard,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_dashboard(self, session: UserSession) -> None:
        """Display the post-authentication dashboard placeholder."""
        self.current_session = session
        self._clear_view()
        self.current_view = DashboardPlaceholderFrame(
            master=self,
            user_session=session,
            on_logout=self.handle_logout,
        )
        self.current_view.pack(fill="both", expand=True)

    def handle_logout(self) -> None:
        """Log out the current user, invalidate session token, and return to login screen."""
        if self.current_session:
            logout_user(self.current_session.id, custom_path=self.db_path)
            self.current_session = None
        self.show_login()


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
