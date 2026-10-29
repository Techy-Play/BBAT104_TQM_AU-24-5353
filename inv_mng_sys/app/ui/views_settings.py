"""Settings view: Profile modifications, session preferences, and password updates."""

from __future__ import annotations

import logging
from typing import Callable, Optional
import customtkinter as ctk

from app.authentication.security import UserSession
from app.settings.settings import SettingsService
from app.ui.components import (
    CardFrame,
    DangerButton,
    LabeledEntry,
    MessageBanner,
    PrimaryButton,
    SecondaryButton,
    setup_form_keyboard_navigation,
)
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    THEME_DROPDOWN_OPTIONS,
    THEME_MODES,
    get_theme_display_string,
    parse_theme_mode,
)

logger = logging.getLogger(__name__)


class DeleteAccountModal(ctk.CTkToplevel):
    """Modal dialog prompting user with explicit warning and password confirmation to delete account and database."""

    def __init__(
        self,
        parent,
        user_session: UserSession,
        on_confirmed: Callable[[], None],
        db_path: Optional[str] = None,
    ):
        super().__init__(parent)
        self.user_session = user_session
        self.on_confirmed = on_confirmed
        self.db_path = db_path

        self.title("Confirm Account & Database Deletion")
        width, height = 540, 410
        self.minsize(500, 370)
        self.resizable(False, False)
        self.transient(parent)

        # Center on parent in single atomic geometry calculation
        try:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            pos_x = max(0, parent_x + (parent_w - width) // 2)
            pos_y = max(0, parent_y + (parent_h - height) // 2)
            self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        except Exception:
            self.geometry(f"{width}x{height}")

        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        card = CardFrame(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Danger Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 6))

        ctk.CTkLabel(
            header,
            text="⚠️ Delete Account & Reset Database",
            font=FONT_HEADING,
            text_color=COLOR_DANGER,
        ).pack(anchor="w")

        # Explicit Warning Callout Box
        warning_box = ctk.CTkFrame(card, fg_color=COLOR_SECONDARY, corner_radius=6)
        warning_box.pack(fill="x", padx=20, pady=(0, 10))

        warning_text = (
            "ATTENTION: This action is permanent and IRREVERSIBLE.\n\n"
            f"• All inventory records and stored products will be permanently erased.\n"
            f"• Your user account (@{self.user_session.username}) will be deleted.\n"
            "• Active sessions will be terminated with NO WAY to recover data.\n\n"
            "The application will freshly restart and present the First-Run Setup wizard."
        )
        ctk.CTkLabel(
            warning_box,
            text=warning_text,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            wraplength=460,
        ).pack(padx=14, pady=10, anchor="w")

        # Password confirmation input
        self.entry_pwd = LabeledEntry(
            card,
            label_text="Enter Your Current Password to Confirm",
            is_password=True,
            placeholder="Type your current password",
            width=460,
        )
        self.entry_pwd.pack(padx=20, pady=(0, 4))

        # Feedback banner
        self.banner = MessageBanner(card)
        self.banner.pack(fill="x", padx=20, pady=(0, 4))

        # Action Buttons Footer
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", padx=20, pady=(6, 16))

        self.btn_cancel = SecondaryButton(
            btn_row,
            text="Cancel",
            command=self.destroy,
            width=100,
            height=34,
        )
        self.btn_cancel.pack(side="right", padx=(10, 0))

        self.btn_delete = DangerButton(
            btn_row,
            text="Permanently Delete Everything",
            command=self._handle_confirm_delete,
            width=230,
            height=34,
        )
        self.btn_delete.pack(side="right")

        # Fast keyboard navigation
        setup_form_keyboard_navigation(
            widgets=[self.entry_pwd, self.btn_delete, self.btn_cancel],
            on_submit=self._handle_confirm_delete,
            on_cancel=self.destroy,
            toplevel=self,
        )
        self.btn_delete.bind("<Return>", lambda _e: (self._handle_confirm_delete(), "break")[1])
        self.btn_delete.bind("<space>", lambda _e: (self._handle_confirm_delete(), "break")[1])
        self.btn_cancel.bind("<Return>", lambda _e: (self.destroy(), "break")[1])
        self.btn_cancel.bind("<space>", lambda _e: (self.destroy(), "break")[1])

        # Immediate auto-focus for instant typing
        self._focus_after_id = self.after(50, self.entry_pwd.focus)

    def destroy(self):
        try:
            if hasattr(self, "_focus_after_id") and self._focus_after_id:
                self.after_cancel(self._focus_after_id)
        except Exception:
            pass
        super().destroy()

    def _handle_confirm_delete(self) -> None:
        self.banner.clear()
        pwd = self.entry_pwd.get_value()

        if not pwd:
            self.banner.show_error("Please enter your current password to confirm deletion.")
            return

        try:
            SettingsService.delete_user_and_reset_database(
                user_id=self.user_session.id,
                password=pwd,
                custom_path=self.db_path,
            )
            # Destroy modal
            self.destroy()
            # Trigger application restart/reroute to setup
            self.on_confirmed()
        except ValueError as val_err:
            self.banner.show_error(str(val_err))
        except Exception as exc:
            logger.exception("Failed to delete account.")
            self.banner.show_error(f"Account deletion failed: {exc}")


class SettingsView(ctk.CTkScrollableFrame):
    """Application settings and user profile management view."""

    def __init__(
        self,
        master,
        user_session: UserSession,
        on_profile_updated: Callable[[UserSession], None],
        on_account_deleted: Optional[Callable[[], None]] = None,
        db_path: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.user_session = user_session
        self.on_profile_updated = on_profile_updated
        self.on_account_deleted = on_account_deleted
        self.db_path = db_path

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

        # Setup Tab navigation and Enter hotkey for profile fields
        setup_form_keyboard_navigation(
            widgets=[self.entry_name, self.entry_org, btn_save_p],
            on_submit=self._handle_save_profile,
        )
        btn_save_p.bind("<Return>", lambda _e: (self._handle_save_profile(), "break")[1])
        btn_save_p.bind("<space>", lambda _e: (self._handle_save_profile(), "break")[1])

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

        # Appearance & Theme Settings Card
        card_theme = CardFrame(container)
        card_theme.pack(fill="x", pady=(0, 15))

        t_title = ctk.CTkLabel(card_theme, text="Appearance & Visual Theme", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY)
        t_title.pack(anchor="w", padx=20, pady=(18, 6))

        t_desc = ctk.CTkLabel(
            card_theme,
            text="Switch between System Default (Device Appearance), Dark Mode, or Light Mode. Your selection is saved persistently across sessions.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            wraplength=550,
            justify="left",
        )
        t_desc.pack(anchor="w", padx=20, pady=(0, 12))

        t_box = ctk.CTkFrame(card_theme, fg_color="transparent")
        t_box.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(t_box, text="Selected Theme:", font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, width=130, anchor="w").pack(side="left")

        current_theme_key = SettingsService.get_theme_preference(custom_path=self.db_path)
        self.opt_theme = ctk.CTkOptionMenu(
            t_box,
            values=THEME_DROPDOWN_OPTIONS,
            command=self._handle_theme_change,
            width=230,
            height=34,
            corner_radius=6,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY_HOVER,
            button_hover_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_hover_color=COLOR_PRIMARY,
        )
        self.opt_theme.set(get_theme_display_string(current_theme_key))
        self.opt_theme.pack(side="left")

        self.theme_banner = MessageBanner(card_theme)
        self.theme_banner.pack(anchor="w", padx=20, pady=(0, 16))

        # Security Card (Password Change)
        card_sec = CardFrame(container)
        card_sec.pack(fill="x", pady=(0, 15))

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

        # Setup Tab navigation and Enter hotkey for password fields
        setup_form_keyboard_navigation(
            widgets=[
                self.entry_curr_pwd,
                self.entry_new_pwd,
                self.entry_conf_pwd,
                btn_change_pwd,
            ],
            on_submit=self._handle_change_password,
        )
        btn_change_pwd.bind("<Return>", lambda _e: (self._handle_change_password(), "break")[1])
        btn_change_pwd.bind("<space>", lambda _e: (self._handle_change_password(), "break")[1])

        # System & Quality Info Card
        card_info = CardFrame(container)
        card_info.pack(fill="x", pady=(0, 20))

        info_title = ctk.CTkLabel(card_info, text="System & Quality Information", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY)
        info_title.pack(anchor="w", padx=20, pady=(18, 10))

        infos = [
            ("Course Project", "BBAT104 Fundamentals of Total Quality Management"),
            ("Assigned Quality Goal", "Q13 — Faster Search & Retrieval"),
            ("Operation Mode", "Fully Offline Desktop Application"),
            ("Database Engine", "SQLite3 (Persistent local storage, WAL mode, B-Tree indexes)"),
            ("Presentation Layer", "CustomTkinter 5.2.2 (Themeable responsive desktop GUI)"),
        ]
        for k, v in infos:
            i_row = ctk.CTkFrame(card_info, fg_color="transparent")
            i_row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(i_row, text=f"{k}:", font=FONT_BODY, text_color=COLOR_TEXT_MUTED, width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(i_row, text=v, font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")

        ctk.CTkLabel(card_info, text="").pack(pady=4)

        # Danger Zone Card (Delete Account & Reset Database)
        card_danger = CardFrame(container)
        card_danger.pack(fill="x", pady=(0, 20))

        d_title = ctk.CTkLabel(
            card_danger,
            text="⚠️ Danger Zone: Delete Account & Reset Database",
            font=FONT_SECTION,
            text_color=COLOR_DANGER,
        )
        d_title.pack(anchor="w", padx=20, pady=(18, 6))

        d_desc = ctk.CTkLabel(
            card_danger,
            text="Permanently delete your user account and wipe the entire local inventory database. All stored products, categories, active sessions, and local data will be permanently erased. This action cannot be reversed.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            wraplength=600,
            justify="left",
        )
        d_desc.pack(anchor="w", padx=20, pady=(0, 14))

        self.btn_delete_user = DangerButton(
            card_danger,
            text="Delete User & Reset Database",
            command=self._handle_open_delete_modal,
            width=230,
            height=36,
        )
        self.btn_delete_user.pack(anchor="w", padx=20, pady=(0, 20))

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

    def _handle_theme_change(self, selected_display: str) -> None:
        """Dynamically toggle and persist appearance mode across CustomTkinter UI."""
        mode = parse_theme_mode(selected_display)
        logger.info("Switching appearance mode to '%s' (selected: %s)", mode, selected_display)
        SettingsService.set_theme_preference(mode, custom_path=self.db_path)
        ctk.set_appearance_mode(mode)
        item = THEME_MODES.get(mode, THEME_MODES["system"])
        self.theme_banner.show_success(f"{item['symbol']} {item['display_name']} applied and saved successfully.")

    def _handle_open_delete_modal(self) -> None:
        """Open the password-protected account deletion confirmation dialog."""
        DeleteAccountModal(
            parent=self.winfo_toplevel(),
            user_session=self.user_session,
            on_confirmed=self._on_account_deleted_callback,
            db_path=self.db_path,
        )

    def _on_account_deleted_callback(self) -> None:
        """Propagate account deletion event to top-level application coordinator."""
        if self.on_account_deleted:
            self.on_account_deleted()
