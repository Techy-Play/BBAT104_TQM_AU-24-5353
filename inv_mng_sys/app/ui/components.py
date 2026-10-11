"""Reusable CustomTkinter UI widgets and layout components."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Union
import customtkinter as ctk

from app.ui.theme import (
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_SUCCESS,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_STAT_TITLE,
    FONT_STAT_VALUE,
    FONT_SUBTITLE,
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
            height=38,
            corner_radius=8,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=FONT_BUTTON,
            **kwargs,
        )


class SecondaryButton(ctk.CTkButton):
    """Standardized secondary button."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, width: int = 120, **kwargs):
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


class DangerButton(ctk.CTkButton):
    """Standardized destructive action button."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, width: int = 120, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=36,
            corner_radius=8,
            fg_color=COLOR_DANGER,
            hover_color=("#991b1b", "#7f1d1d"),
            text_color="#ffffff",
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
            wraplength=380,
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


class StatCard(CardFrame):
    """Dashboard statistic card displaying icon, numeric metric, and title."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        icon: str,
        accent_color=COLOR_PRIMARY,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.accent_color = accent_color

        # Top row: Icon and title
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=16, pady=(14, 4))

        icon_lbl = ctk.CTkLabel(
            top_frame,
            text=icon,
            font=(FONT_BODY[0], 20),
            text_color=self.accent_color,
        )
        icon_lbl.pack(side="left")

        title_lbl = ctk.CTkLabel(
            top_frame,
            text=title,
            font=FONT_STAT_TITLE,
            text_color=COLOR_TEXT_MUTED,
        )
        title_lbl.pack(side="left", padx=(8, 0))

        # Value display
        self.val_lbl = ctk.CTkLabel(
            self,
            text=str(value),
            font=FONT_STAT_VALUE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.val_lbl.pack(anchor="w", padx=16, pady=(4, 14))

    def update_value(self, new_val: Union[str, int, float]) -> None:
        """Dynamically update metric value."""
        self.val_lbl.configure(text=str(new_val))


class StatusBadge(ctk.CTkFrame):
    """Pill-shaped badge indicating product stock status."""

    def __init__(self, master, status: str, **kwargs):
        status_colors = {
            "In Stock": COLOR_SUCCESS,
            "Low Stock": COLOR_WARNING,
            "Out of Stock": COLOR_DANGER,
        }
        accent = status_colors.get(status, COLOR_SECONDARY)

        super().__init__(
            master,
            corner_radius=12,
            fg_color=accent,
            height=26,
            **kwargs,
        )
        self.pack_propagate(False)

        lbl = ctk.CTkLabel(
            self,
            text=f"  {status}  ",
            font=FONT_SMALL,
            text_color="#ffffff",
        )
        lbl.pack(expand=True)


class ConfirmationModal(ctk.CTkToplevel):
    """Modal dialog for confirmation of actions (e.g., deletion)."""

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        confirm_callback: Callable[[], None],
        confirm_text: str = "Confirm",
        danger: bool = True,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 210
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 110
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        card = CardFrame(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        title_lbl = ctk.CTkLabel(card, text=title, font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY)
        title_lbl.pack(anchor="w", padx=16, pady=(16, 8))

        msg_lbl = ctk.CTkLabel(
            card,
            text=message,
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
            wraplength=350,
            justify="left",
        )
        msg_lbl.pack(anchor="w", padx=16, pady=(0, 20))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        btn_cancel = SecondaryButton(btn_row, text="Cancel", command=self.destroy, width=100)
        btn_cancel.pack(side="right", padx=(8, 0))

        def _on_confirm():
            self.destroy()
            confirm_callback()

        if danger:
            btn_confirm = DangerButton(btn_row, text=confirm_text, command=_on_confirm, width=120)
        else:
            btn_confirm = PrimaryButton(btn_row, text=confirm_text, command=_on_confirm, width=120)
        btn_confirm.pack(side="right")
