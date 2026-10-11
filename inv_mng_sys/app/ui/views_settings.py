"""Settings view: Profile modifications, session preferences, and password updates."""

from __future__ import annotations

import logging
from typing import Callable, Optional
import customtkinter as ctk

from app.authentication.security import UserSession
from app.settings.settings import SettingsService
from app.ui.components import (
    CardFrame,
    LabeledEntry,
    MessageBanner,
    PrimaryButton,
    SecondaryButton,
)
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
)

logger = logging.getLogger(__name__)


class SettingsView(ctk.CTkScrollableFrame):
    """Application settings and user profile management view."""

    def __init__(
        self,
        master,
        user_session: UserSession,
        on_profile_updated: Callable[[UserSession], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.user_session = user_session
        self.on_profile_updated = on_profile_updated

        self._build_ui()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=15)

        # Header
        head_box = CardFrame(container)
        head_box.pack(fill="x", pady=(0, 15))

        title = ctk.CTkLabel(head_box, text="⚙️ Application Settings", font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY)
        title.pack(anchor="w", padx=20, pady=(16, 4))

        sub = ctk.CTkLabel(
            head_box,
            text="Manage your personal profile, business identity, and local security preferences.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        sub.pack(anchor="w", padx=20, pady=(0, 16))

        # Profile Card
        card_profile = CardFrame(container)
        card_profile.pack(fill="x", pady=(0, 15))

        p_title = ctk.CTkLabel(card_profile, text="User & Business Profile", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY)
        p_title.pack(anchor="w", padx=20, pady=(18, 12))

        # Username (Read-only)
        u_box = ctk.CTkFrame(card_profile, fg_color="transparent")
        u_box.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(u_box, text="Username (Account ID):", font=FONT_BODY, text_color=COLOR_TEXT_MUTED, width=180, anchor="w").pack(side="left")
        ctk.CTkLabel(u_box, text=f"@{self.user_session.username}", font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")

        self.entry_name = LabeledEntry(
            card_profile,
            label_text="Full Name",
            placeholder="e.g. Lokesh Paneru",
            width=420,
        )
        self.entry_name.pack(padx=20, pady=6)
        self.entry_name.set_value(self.user_session.full_name)

        self.entry_org = LabeledEntry(
            card_profile,
            label_text="Store / Warehouse / Business Name",
            placeholder="e.g. Apex Hardware",
            width=420,
        )
        self.entry_org.pack(padx=20, pady=6)
        self.entry_org.set_value(self.user_session.organization_name)

        self.profile_banner = MessageBanner(card_profile)
        self.profile_banner.pack(padx=20, pady=4)

        btn_save_p = PrimaryButton(
            card_profile,
            text="Save Profile Changes",
            command=self._handle_save_profile,
            width=200,
        )
        btn_save_p.pack(anchor="w", padx=20, pady=(8, 20))

        # Session & Preferences Card
        card_prefs = CardFrame(container)
        card_prefs.pack(fill="x", pady=(0, 15))

        pref_title = ctk.CTkLabel(card_prefs, text="Local Session Preferences", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY)
        pref_title.pack(anchor="w", padx=20, pady=(18, 8))

        self.chk_keep = ctk.CTkCheckBox(
            card_prefs,
            text="Keep Me Logged In on this computer",
            font=FONT_BODY,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=4,
        )
        self.chk_keep.pack(anchor="w", padx=20, pady=10)
        if self.user_session.keep_logged_in:
            self.chk_keep.select()
        else:
            self.chk_keep.deselect()

        self.pref_banner = MessageBanner(card_prefs)
        self.pref_banner.pack(padx=20, pady=4)

        btn_save_pref = SecondaryButton(
            card_prefs,
            text="Update Preference",
            command=self._handle_save_prefs,
            width=160,
        )
        btn_save_pref.pack(anchor="w", padx=20, pady=(4, 20))

        # Security Card (Password Change)
        card_sec = CardFrame(container)
        card_sec.pack(fill="x", pady=(0, 20))

        sec_title = ctk.CTkLabel(card_sec, text="Security & Password", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY)
        sec_title.pack(anchor="w", padx=20, pady=(18, 12))

        self.entry_curr_pwd = LabeledEntry(
            card_sec,
            label_text="Current Password",
            is_password=True,
            width=420,
        )
        self.entry_curr_pwd.pack(padx=20, pady=6)

        self.entry_new_pwd = LabeledEntry(
            card_sec,
            label_text="New Password (min 6 characters)",
            is_password=True,
            width=420,
        )
        self.entry_new_pwd.pack(padx=20, pady=6)

        self.entry_conf_pwd = LabeledEntry(
            card_sec,
            label_text="Confirm New Password",
            is_password=True,
            width=420,
        )
        self.entry_conf_pwd.pack(padx=20, pady=6)

        self.sec_banner = MessageBanner(card_sec)
        self.sec_banner.pack(padx=20, pady=4)

        btn_change_pwd = PrimaryButton(
            card_sec,
            text="Change Password",
            command=self._handle_change_password,
            width=180,
        )
        btn_change_pwd.pack(anchor="w", padx=20, pady=(8, 20))

    def _handle_save_profile(self) -> None:
        self.profile_banner.clear()
        name = self.entry_name.get_value().strip()
        org = self.entry_org.get_value().strip()

        try:
            updated = SettingsService.update_profile(self.user_session.id, name, org)
            self.user_session = updated
            self.on_profile_updated(updated)
            self.profile_banner.show_success("Profile updated successfully.")
        except ValueError as err:
            self.profile_banner.show_error(str(err))
        except Exception as exc:
            logger.exception("Error updating profile.")
            self.profile_banner.show_error(f"Failed to update profile: {exc}")

    def _handle_save_prefs(self) -> None:
        self.pref_banner.clear()
        keep = bool(self.chk_keep.get())

        try:
            updated = SettingsService.update_session_preference(self.user_session.id, keep)
            self.user_session = updated
            self.on_profile_updated(updated)
            self.pref_banner.show_success("Session preference updated successfully.")
        except Exception as exc:
            logger.exception("Error updating session preference.")
            self.pref_banner.show_error(f"Failed to update preference: {exc}")

    def _handle_change_password(self) -> None:
        self.sec_banner.clear()
        curr_pwd = self.entry_curr_pwd.get_value()
        new_pwd = self.entry_new_pwd.get_value()
        conf_pwd = self.entry_conf_pwd.get_value()

        try:
            SettingsService.change_password(
                user_id=self.user_session.id,
                current_password=curr_pwd,
                new_password=new_pwd,
                confirm_password=conf_pwd,
            )
            self.entry_curr_pwd.set_value("")
            self.entry_new_pwd.set_value("")
            self.entry_conf_pwd.set_value("")
            self.sec_banner.show_success("Password changed successfully.")
        except ValueError as err:
            self.sec_banner.show_error(str(err))
        except Exception as exc:
            logger.exception("Error changing password.")
            self.sec_banner.show_error(f"Failed to change password: {exc}")
