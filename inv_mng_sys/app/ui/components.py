"""Reusable CustomTkinter UI widgets and layout components."""

from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_SUCCESS,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BUTTON,
    FONT_SMALL,
)


class CardFrame(ctk.CTkFrame):
    """Container frame with styled background and rounded corners."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLOR_CARD_BG)
        kwargs.setdefault("corner_radius", 12)
        super().__init__(master, **kwargs)


class LabeledEntry(ctk.CTkFrame):
    """Reusable input group with label and styled entry field."""

    def __init__(
        self,
        master,
        label_text: str,
        placeholder: str = "",
        is_password: bool = False,
        width: int = 340,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=FONT_BODY,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.label.pack(fill="x", padx=2, pady=(0, 4))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            show="*" if is_password else "",
            width=width,
            height=38,
            corner_radius=8,
            font=FONT_BODY,
        )
        self.entry.pack(fill="x", padx=2, pady=(0, 2))

    def get_value(self) -> str:
        """Get the trimmed entry text."""
        return self.entry.get()

    def set_value(self, val: str) -> None:
        """Set entry text."""
        self.entry.delete(0, "end")
        self.entry.insert(0, val)

    def focus(self) -> None:
        """Give focus to the internal entry field."""
        self.entry.focus()


class PrimaryButton(ctk.CTkButton):
    """Standardized primary action button."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, width: int = 340, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=40,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=FONT_BUTTON,
            **kwargs,
        )


class SecondaryButton(ctk.CTkButton):
    """Standardized secondary button."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, width: int = 140, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=36,
            corner_radius=8,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            font=FONT_BUTTON,
            **kwargs,
        )


class MessageBanner(ctk.CTkLabel):
    """Status/error banner that can be shown or cleared dynamically."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            text="",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_ERROR,
            wraplength=340,
            **kwargs,
        )

    def show_error(self, message: str) -> None:
        """Display an error message in red."""
        self.configure(text=message, text_color=COLOR_TEXT_ERROR)

    def show_success(self, message: str) -> None:
        """Display a success message in green."""
        self.configure(text=message, text_color=COLOR_SUCCESS)

    def clear(self) -> None:
        """Clear the banner text."""
        self.configure(text="")
