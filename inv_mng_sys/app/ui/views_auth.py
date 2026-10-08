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


class FirstRunSetupFrame(ctk.CTkScrollableFrame):
    """First-run setup wizard frame collecting profile and security credentials."""

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
        container = CardFrame(self, width=460)
        container.pack(expand=True, pady=30, padx=20)

        # Title and intro
        title = ctk.CTkLabel(
            container,
            text="Welcome to IMS",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        title.pack(pady=(28, 4))

        subtitle = ctk.CTkLabel(
            container,
            text="Initial First-Run Setup (Offline Local Database)",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle.pack(pady=(0, 20))

        # Instructions callout
        desc = ctk.CTkLabel(
            container,
            text="Configure your local profile and secure your inventory system.\nAll data is stored locally on this machine.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            justify="center",
        )
        desc.pack(pady=(0, 20), padx=25)

        # Form fields
        self.entry_name = LabeledEntry(
            container,
            label_text="User / Full Name",
            placeholder="e.g. Lokesh Paneru",
            width=380,
        )
        self.entry_name.pack(pady=6)

        self.entry_org = LabeledEntry(
            container,
            label_text="Store / Warehouse / Business Name",
            placeholder="e.g. Apex Hardware & Electronics",
            width=380,
        )
        self.entry_org.pack(pady=6)

        self.entry_user = LabeledEntry(
            container,
            label_text="Username",
            placeholder="e.g. admin",
            width=380,
        )
        self.entry_user.pack(pady=6)

        self.entry_pwd = LabeledEntry(
            container,
            label_text="Password",
            placeholder="At least 6 characters",
            is_password=True,
            width=380,
        )
        self.entry_pwd.pack(pady=6)

        self.entry_confirm = LabeledEntry(
            container,
            label_text="Confirm Password",
            placeholder="Re-enter password",
            is_password=True,
            width=380,
        )
        self.entry_confirm.pack(pady=6)

        # Keep Me Logged In checkbox
        self.chk_keep_logged_in = ctk.CTkCheckBox(
            container,
            text="Keep Me Logged In on this computer",
            font=FONT_BODY,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=4,
        )
        self.chk_keep_logged_in.pack(pady=12, padx=25, anchor="w")

        # Feedback banner
        self.banner = MessageBanner(container)
        self.banner.pack(pady=(4, 8), padx=20)

        # Action button
        self.btn_submit = PrimaryButton(
            container,
            text="Complete Setup & Launch",
            command=self._handle_setup,
            width=380,
        )
        self.btn_submit.pack(pady=(8, 28))

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
        container = CardFrame(self, width=420)
        container.pack(expand=True, pady=40, padx=20)

        # Header
        title = ctk.CTkLabel(
            container,
            text="Inventory Management System",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        title.pack(pady=(32, 4))

        subtitle = ctk.CTkLabel(
            container,
            text="BBAT104 — Offline Desktop Access",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle.pack(pady=(0, 24))

        # Fields
        self.entry_user = LabeledEntry(
            container,
            label_text="Username",
            placeholder="Enter your username",
            width=340,
        )
        self.entry_user.pack(pady=8)

        self.entry_pwd = LabeledEntry(
            container,
            label_text="Password",
            placeholder="Enter your password",
            is_password=True,
            width=340,
        )
        self.entry_pwd.pack(pady=8)

        # Bind Enter key to submit
        self.entry_pwd.entry.bind("<Return>", lambda event: self._handle_login())
        self.entry_user.entry.bind("<Return>", lambda event: self._handle_login())

        # Keep Me Logged In preference
        self.chk_keep_logged_in = ctk.CTkCheckBox(
            container,
            text="Keep Me Logged In",
            font=FONT_BODY,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=4,
        )
        self.chk_keep_logged_in.pack(pady=12, padx=30, anchor="w")

        # Feedback banner
        self.banner = MessageBanner(container)
        self.banner.pack(pady=(4, 8), padx=20)

        # Submit button
        self.btn_login = PrimaryButton(
            container,
            text="Sign In",
            command=self._handle_login,
            width=340,
        )
        self.btn_login.pack(pady=(8, 32))

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
