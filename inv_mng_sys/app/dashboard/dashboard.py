"""Dashboard view and placeholder for post-authentication home screen.

Receives authenticated UserSession and provides logout capabilities.
Prepares the workspace for Phase 5 (Full Dashboard & Statistics).
"""

from __future__ import annotations

import logging
from typing import Callable
import customtkinter as ctk

from app.authentication.security import UserSession
from app.ui.components import CardFrame, SecondaryButton
from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SURFACE_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_TITLE,
)

logger = logging.getLogger(__name__)


class DashboardPlaceholderFrame(ctk.CTkFrame):
    """Placeholder dashboard displaying active user profile and session info."""

    def __init__(
        self,
        master,
        user_session: UserSession,
        on_logout: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.user_session = user_session
        self.on_logout = on_logout

        self._build_ui()

    def _build_ui(self) -> None:
        # Top Navigation Bar
        nav_bar = CardFrame(self, height=65)
        nav_bar.pack(fill="x", padx=25, pady=(20, 15))
        nav_bar.pack_propagate(False)

        brand_label = ctk.CTkLabel(
            nav_bar,
            text=f"📦  {self.user_session.organization_name}",
            font=FONT_HEADING,
            text_color=COLOR_TEXT_PRIMARY,
        )
        brand_label.pack(side="left", padx=20)

        # Right side: user info and logout
        user_tag = ctk.CTkLabel(
            nav_bar,
            text=f"👤 {self.user_session.full_name} (@{self.user_session.username})",
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
        )
        user_tag.pack(side="left", padx=(15, 0))

        btn_logout = ctk.CTkButton(
            nav_bar,
            text="Log Out",
            command=self.on_logout,
            width=100,
            height=34,
            corner_radius=6,
            fg_color=COLOR_DANGER,
            hover_color=("#991b1b", "#7f1d1d"),
            font=FONT_BUTTON,
        )
        btn_logout.pack(side="right", padx=20)

        # Main Content Area
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=10)

        # Welcome Hero Card
        hero_card = CardFrame(content)
        hero_card.pack(fill="x", pady=(0, 15), padx=0)

        welcome_text = ctk.CTkLabel(
            hero_card,
            text=f"Good day, {self.user_session.full_name}!",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        welcome_text.pack(anchor="w", padx=25, pady=(20, 4))

        org_subtitle = ctk.CTkLabel(
            hero_card,
            text=f"Welcome to your offline Inventory Management System for {self.user_session.organization_name}.",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_MUTED,
        )
        org_subtitle.pack(anchor="w", padx=25, pady=(0, 20))

        # Status & Profile Overview
        grid_frame = ctk.CTkFrame(content, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure((0, 1), weight=1)

        # Profile Card
        profile_card = CardFrame(grid_frame)
        profile_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        profile_title = ctk.CTkLabel(
            profile_card,
            text="User Profile Details",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        )
        profile_title.pack(anchor="w", padx=20, pady=(18, 12))

        details = [
            ("Full Name", self.user_session.full_name),
            ("Store / Entity", self.user_session.organization_name),
            ("Username", f"@{self.user_session.username}"),
            (
                "Keep Me Logged In",
                "Enabled" if self.user_session.keep_logged_in else "Disabled",
            ),
            ("System Mode", "Offline Local Storage (SQLite3)"),
        ]

        for label, val in details:
            row = ctk.CTkFrame(profile_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            lbl = ctk.CTkLabel(row, text=f"{label}:", font=FONT_BODY, text_color=COLOR_TEXT_MUTED, width=150, anchor="w")
            lbl.pack(side="left")
            val_lbl = ctk.CTkLabel(row, text=val, font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, anchor="w")
            val_lbl.pack(side="left")

        # Project Status Card
        status_card = CardFrame(grid_frame)
        status_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        status_title = ctk.CTkLabel(
            status_card,
            text="Milestone Verification",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        )
        status_title.pack(anchor="w", padx=20, pady=(18, 12))

        milestones = [
            ("Phase 1: Project Architecture", "Verified ✓"),
            ("Phase 2: Persistent SQLite & Q13 Indexes", "Verified ✓"),
            ("Phase 3: First-Run Setup & Profile Storage", "Active ✓"),
            ("Phase 4: PBKDF2 Hashing & Local Sessions", "Active ✓"),
            ("Phase 5: Full Dashboard & Statistics", "Upcoming"),
            ("Phase 6: Inventory CRUD Operations", "Upcoming"),
        ]

        for phase, state in milestones:
            row = ctk.CTkFrame(status_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            color = COLOR_SUCCESS if "✓" in state else COLOR_TEXT_MUTED
            lbl = ctk.CTkLabel(row, text=phase, font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, anchor="w")
            lbl.pack(side="left")
            tag = ctk.CTkLabel(row, text=state, font=FONT_BODY, text_color=color, anchor="e")
            tag.pack(side="right")
