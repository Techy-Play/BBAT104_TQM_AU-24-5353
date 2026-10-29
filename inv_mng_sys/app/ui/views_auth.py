"""Authentication GUI screens for First-Run Setup and User Login."""

from __future__ import annotations

import logging
from typing import Callable, Optional
import customtkinter as ctk

from app.authentication.login import authenticate_user
from app.authentication.security import UserSession
from app.authentication.setup import register_first_user
from app.ui.components import (
    CardFrame,
    LabeledEntry,
    MessageBanner,
    PrimaryButton,
    setup_form_keyboard_navigation,
)
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_SURFACE_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_TITLE,
)

logger = logging.getLogger(__name__)


class FirstRunSetupFrame(ctk.CTkFrame):
    """First-run setup wizard frame collecting profile and security credentials in a clean non-scrolling card."""

    def __init__(
        self,
        master,
        on_success: Callable[[UserSession], None],
        reset_notice: bool = False,
        db_path: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_success = on_success
        self.reset_notice = reset_notice
        self.db_path = db_path

        self._build_ui()

    def _build_ui(self) -> None:
        container = CardFrame(self, width=640)
        container.pack(expand=True, padx=20, pady=16)

        # Title & Subtitle Header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 6))

        title = ctk.CTkLabel(
            header_frame,
            text="📦 Inventory Management System",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Initial First-Run Setup • Secure Offline Local Storage",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # 2-Column Responsive Form Grid (All fields visible at once without scrolling)
        form_grid = ctk.CTkFrame(container, fg_color="transparent")
        form_grid.pack(fill="x", padx=20, pady=(8, 4))
        form_grid.grid_columnconfigure((0, 1), weight=1, uniform="col_setup")

        # Column 0: User & Store Identity
        self.entry_name = LabeledEntry(
            form_grid,
            label_text="User / Full Name *",
            placeholder="e.g. Lokesh Paneru",
            width=280,
        )
        self.entry_name.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=4)

        self.entry_org = LabeledEntry(
            form_grid,
            label_text="Store / Business Name *",
            placeholder="e.g. Apex Hardware",
            width=280,
        )
        self.entry_org.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=4)

        self.entry_user = LabeledEntry(
            form_grid,
            label_text="Username (Account ID) *",
            placeholder="e.g. admin",
            width=280,
        )
        self.entry_user.grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=4)

        # Column 1: Password & Security
        self.entry_pwd = LabeledEntry(
            form_grid,
            label_text="Password (min 6 chars) *",
            placeholder="Create master password",
            is_password=True,
            width=280,
        )
        self.entry_pwd.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        self.entry_confirm = LabeledEntry(
            form_grid,
            label_text="Confirm Password *",
            placeholder="Re-enter password",
            is_password=True,
            width=280,
        )
        self.entry_confirm.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        # Preferences row in Column 1
        pref_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        pref_box.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=4)

        self.chk_keep_logged_in = ctk.CTkCheckBox(
            pref_box,
            text="Keep Me Logged In on this PC",
            font=FONT_BODY,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=4,
        )
        self.chk_keep_logged_in.pack(anchor="w", pady=(8, 2))
        self.chk_keep_logged_in.select()

        # Security Callout Box
        security_callout = ctk.CTkFrame(container, fg_color=COLOR_SURFACE_BG, corner_radius=6)
        security_callout.pack(fill="x", padx=20, pady=(6, 4))
        ctk.CTkLabel(
            security_callout,
            text="🔒 Offline Local Security: Salted PBKDF2 (SHA-256) password encryption. No internet connection required.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        ).pack(padx=12, pady=6)

        # Feedback banner
        self.banner = MessageBanner(container)
        self.banner.pack(fill="x", padx=20, pady=(4, 4))
        if self.reset_notice:
            self.banner.show_info("Database and user account were reset. Please configure your new administrator profile.")

        # Action button
        self.btn_submit = PrimaryButton(
            container,
            text="Complete Setup & Launch System",
            command=self._handle_setup,
            width=300,
            height=36,
        )
        self.btn_submit.pack(pady=(6, 4))

        # Keyboard shortcut hint
        hint_lbl = ctk.CTkLabel(
            container,
            text="⌨️ Tab: Next field • Shift+Tab: Prev • Enter: Complete Setup",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        hint_lbl.pack(pady=(0, 16))

        # Setup Tab/Shift-Tab keyboard navigation and Enter hotkey
        setup_form_keyboard_navigation(
            widgets=[
                self.entry_name,
                self.entry_org,
                self.entry_user,
                self.entry_pwd,
                self.entry_confirm,
                self.chk_keep_logged_in,
                self.btn_submit,
            ],
            on_submit=self._handle_setup,
        )
        self.btn_submit.bind("<Return>", lambda _e: (self._handle_setup(), "break")[1])
        self.btn_submit.bind("<space>", lambda _e: (self._handle_setup(), "break")[1])
        self._focus_after_id = self.after(50, self.entry_name.focus)

    def destroy(self):
        try:
            if hasattr(self, "_focus_after_id") and self._focus_after_id:
                self.after_cancel(self._focus_after_id)
                self._focus_after_id = None
        except Exception:
            pass
        super().destroy()

    def _handle_setup(self) -> None:
        self.banner.clear()

        full_name = self.entry_name.get_value()
        org_name = self.entry_org.get_value()
        username = self.entry_user.get_value()
        pwd = self.entry_pwd.get_value()
        confirm = self.entry_confirm.get_value()
        keep = bool(self.chk_keep_logged_in.get())

        try:
            session = register_first_user(
                full_name=full_name,
                org_name=org_name,
                username=username,
                password=pwd,
                confirm_password=confirm,
                keep_logged_in=keep,
                custom_path=self.db_path,
            )
            logger.info("First-run setup completed for '%s'.", session.username)
            self.on_success(session)
        except ValueError as err:
            self.banner.show_error(str(err))
        except Exception as exc:
            logger.exception("Unexpected error during setup.")
            self.banner.show_error("An unexpected error occurred. Please try again.")


class LoginFrame(ctk.CTkFrame):
    """User authentication frame for existing local accounts."""

    def __init__(
        self,
        master,
        on_success: Callable[[UserSession], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_success = on_success

        self._build_ui()

    def _build_ui(self) -> None:
        container = CardFrame(self, width=390, corner_radius=12)
        container.pack(expand=True, padx=24, pady=24)

        # Brand icon badge
        badge_frame = ctk.CTkFrame(
            container,
            fg_color=COLOR_PRIMARY,
            width=50,
            height=50,
            corner_radius=12,
        )
        badge_frame.pack(pady=(28, 10))
        badge_frame.pack_propagate(False)

        badge_icon = ctk.CTkLabel(
            badge_frame,
            text="📦",
            font=(FONT_TITLE[0], 24),
            text_color="#ffffff",
        )
        badge_icon.pack(expand=True)

        # Header
        title = ctk.CTkLabel(
            container,
            text="Welcome Back",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        title.pack(pady=(0, 2))

        subtitle = ctk.CTkLabel(
            container,
            text="BBAT104 • Offline Desktop Access",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle.pack(pady=(0, 16))

        # Form fields container
        form_box = ctk.CTkFrame(container, fg_color="transparent")
        form_box.pack(fill="x", padx=28)

        # Fields
        self.entry_user = LabeledEntry(
            form_box,
            label_text="Username",
            placeholder="Enter your username",
            width=320,
        )
        self.entry_user.pack(fill="x", pady=(0, 8))

        self.entry_pwd = LabeledEntry(
            form_box,
            label_text="Password",
            placeholder="Enter your password",
            is_password=True,
            width=320,
        )
        self.entry_pwd.pack(fill="x", pady=(0, 6))

        # Bind Enter key to submit
        self.entry_pwd.entry.bind("<Return>", lambda event: self._handle_login())
        self.entry_user.entry.bind("<Return>", lambda event: self._handle_login())

        # Keep Me Logged In preference
        self.chk_keep_logged_in = ctk.CTkCheckBox(
            form_box,
            text="Keep Me Logged In on this PC",
            font=FONT_SMALL,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
        )
        self.chk_keep_logged_in.pack(anchor="w", pady=(4, 10))

        # Feedback banner
        self.banner = MessageBanner(form_box)
        self.banner.pack(fill="x", pady=(0, 6))

        # Submit button
        self.btn_login = PrimaryButton(
            form_box,
            text="Sign In",
            command=self._handle_login,
            width=320,
            height=38,
        )
        self.btn_login.pack(fill="x", pady=(2, 14))

        # Setup Tab/Shift-Tab keyboard navigation and Enter hotkey
        setup_form_keyboard_navigation(
            widgets=[
                self.entry_user,
                self.entry_pwd,
                self.chk_keep_logged_in,
                self.btn_login,
            ],
            on_submit=self._handle_login,
        )
        self.btn_login.bind("<Return>", lambda _e: (self._handle_login(), "break")[1])
        self.btn_login.bind("<space>", lambda _e: (self._handle_login(), "break")[1])
        self._focus_after_id = self.after(50, self.entry_user.focus)

        # Footer security tag
        footer = ctk.CTkLabel(
            container,
            text="🔒 Offline SQLite Storage • Quality Assured",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        footer.pack(pady=(0, 22))

    def destroy(self):
        try:
            if hasattr(self, "_focus_after_id") and self._focus_after_id:
                self.after_cancel(self._focus_after_id)
                self._focus_after_id = None
        except Exception:
            pass
        super().destroy()

    def _handle_login(self) -> None:
        self.banner.clear()

        username = self.entry_user.get_value()
        password = self.entry_pwd.get_value()
        keep = bool(self.chk_keep_logged_in.get())

        try:
            session = authenticate_user(
                username=username,
                password=password,
                keep_logged_in=keep,
            )
            logger.info("Login succeeded for user '%s'.", session.username)
            self.on_success(session)
        except ValueError as err:
            self.banner.show_error(str(err))
        except Exception as exc:
            logger.exception("Unexpected error during login.")
            self.banner.show_error("An unexpected error occurred. Please try again.")
