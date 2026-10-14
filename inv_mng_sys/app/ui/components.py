"""Reusable CustomTkinter UI widgets and layout components.

Provides standardized, accessible, and responsive components:
- CardFrame: Container card with subtle border and rounded corners.
- LabeledEntry: Labeled input field with placeholder and validation state.
- PrimaryButton, SecondaryButton, DangerButton: Sized and styled action buttons.
- MessageBanner: Dynamic status and feedback banner.
- StatCard: Standardized metric card for dashboard analytics.
- StatusBadge: Pill badge for product stock statuses.
- ConfirmationModal: Accessible dialog for destructive confirmations.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Union
import customtkinter as ctk

from app.ui.theme import (
    COLOR_BORDER,
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_INFO,
    COLOR_INPUT_BG,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_SUCCESS,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_ON_PRIMARY,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_STAT_TITLE,
    FONT_STAT_VALUE,
    FONT_SUBTITLE,
    HEIGHT_BUTTON_MD,
    HEIGHT_INPUT,
    RADIUS_BADGE,
    RADIUS_BUTTON,
    RADIUS_CARD,
    RADIUS_INPUT,
)


class CardFrame(ctk.CTkFrame):
    """Container frame with styled background, subtle border, and rounded corners."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLOR_CARD_BG)
        kwargs.setdefault("corner_radius", RADIUS_CARD)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLOR_BORDER)
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
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.label.pack(fill="x", padx=1, pady=(0, 4))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            show="*" if is_password else "",
            width=width,
            height=HEIGHT_INPUT,
            corner_radius=RADIUS_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            placeholder_text_color=COLOR_TEXT_MUTED,
            font=FONT_BODY,
        )
        self.entry.pack(fill="x", padx=1, pady=(0, 2))

    def get_value(self) -> str:
        """Get the trimmed entry text."""
        return self.entry.get().strip()

    def set_value(self, val: str) -> None:
        """Set entry text."""
        self.entry.delete(0, "end")
        self.entry.insert(0, val)

    def focus(self) -> None:
        """Give focus to the internal entry field."""
        self.entry.focus()

    def focus_set(self) -> None:
        """Explicitly set keyboard focus on the internal entry widget."""
        self.entry.focus_set()

    def bind(self, sequence=None, func=None, add=None):
        """Bind keyboard and mouse events directly to the entry field."""
        return self.entry.bind(sequence, func, add)


class PrimaryButton(ctk.CTkButton):
    """Standardized primary action button."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, width: int = 120, height: int = HEIGHT_BUTTON_MD, **kwargs):
        kwargs.setdefault("corner_radius", RADIUS_BUTTON)
        kwargs.setdefault("fg_color", COLOR_PRIMARY)
        kwargs.setdefault("hover_color", COLOR_PRIMARY_HOVER)
        kwargs.setdefault("text_color", COLOR_TEXT_ON_PRIMARY)
        kwargs.setdefault("font", FONT_BUTTON)
        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=height,
            **kwargs,
        )


class SecondaryButton(ctk.CTkButton):
    """Standardized secondary button with subtle neutral outline."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, width: int = 110, height: int = HEIGHT_BUTTON_MD, **kwargs):
        kwargs.setdefault("corner_radius", RADIUS_BUTTON)
        kwargs.setdefault("fg_color", COLOR_SECONDARY)
        kwargs.setdefault("hover_color", COLOR_SECONDARY_HOVER)
        kwargs.setdefault("text_color", COLOR_TEXT_PRIMARY)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLOR_BORDER)
        kwargs.setdefault("font", FONT_BUTTON)
        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=height,
            **kwargs,
        )


class DangerButton(ctk.CTkButton):
    """Standardized destructive action button."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, width: int = 110, height: int = HEIGHT_BUTTON_MD, **kwargs):
        kwargs.setdefault("corner_radius", RADIUS_BUTTON)
        kwargs.setdefault("fg_color", COLOR_DANGER)
        kwargs.setdefault("hover_color", COLOR_DANGER_HOVER)
        kwargs.setdefault("text_color", "#ffffff")
        kwargs.setdefault("font", FONT_BUTTON)
        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=height,
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
            wraplength=420,
            justify="center",
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
    """Dashboard statistic card displaying icon, numeric metric, title, and optional deep-link action."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        icon: str,
        accent_color=COLOR_PRIMARY,
        link_text: Optional[str] = None,
        on_click: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.accent_color = accent_color
        self.on_click_callback = on_click

        # Top row: Icon and title
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=14, pady=(12, 2))

        icon_lbl = ctk.CTkLabel(
            top_frame,
            text=icon,
            font=(FONT_BODY[0], 18),
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
        self.val_lbl.pack(anchor="w", padx=14, pady=(2, 2))

        # Optional Deep Link text/indicator
        self.link_lbl: Optional[ctk.CTkLabel] = None
        if link_text or on_click:
            display_link = link_text or "View in Inventory →"
            self.link_lbl = ctk.CTkLabel(
                self,
                text=display_link,
                font=FONT_SMALL,
                text_color=self.accent_color,
                anchor="w",
            )
            self.link_lbl.pack(anchor="w", padx=14, pady=(0, 10))

            self._setup_click_handlers(top_frame, icon_lbl, title_lbl)

    def _setup_click_handlers(self, *widgets) -> None:
        if not self.on_click_callback:
            return

        def _handle_click(_e=None):
            if self.on_click_callback:
                self.on_click_callback()

        def _on_enter(_e=None):
            self.configure(border_color=self.accent_color)
            if self.link_lbl:
                self.link_lbl.configure(font=(FONT_SMALL[0], FONT_SMALL[1], "bold"))

        def _on_leave(_e=None):
            self.configure(border_color=COLOR_BORDER)
            if self.link_lbl:
                self.link_lbl.configure(font=FONT_SMALL)

        clickable_elements = [self, self.val_lbl]
        if self.link_lbl is not None:
            clickable_elements.append(self.link_lbl)
        clickable_elements.extend(widgets)

        for w in clickable_elements:
            if w is not None:
                w.bind("<Button-1>", _handle_click)
                w.bind("<Enter>", _on_enter)
                w.bind("<Leave>", _on_leave)
                try:
                    w.configure(cursor="hand2")
                except Exception:
                    pass

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
            corner_radius=RADIUS_BADGE,
            fg_color=accent,
            height=24,
            width=96,
            **kwargs,
        )
        self.pack_propagate(False)

        lbl = ctk.CTkLabel(
            self,
            text=status,
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
        self.geometry("440x230")
        self.minsize(400, 200)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 220
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 115
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        card = CardFrame(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        title_lbl = ctk.CTkLabel(card, text=title, font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY)
        title_lbl.pack(anchor="w", padx=16, pady=(16, 6))

        msg_lbl = ctk.CTkLabel(
            card,
            text=message,
            font=FONT_BODY,
            text_color=COLOR_TEXT_MUTED,
            wraplength=380,
            justify="left",
        )
        msg_lbl.pack(anchor="w", padx=16, pady=(0, 18))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        btn_cancel = SecondaryButton(btn_row, text="Cancel", command=self.destroy, width=95)
        btn_cancel.pack(side="right", padx=(8, 0))

        def _on_confirm():
            self.destroy()
            confirm_callback()

        if danger:
            btn_confirm = DangerButton(btn_row, text=confirm_text, command=_on_confirm, width=125)
        else:
            btn_confirm = PrimaryButton(btn_row, text=confirm_text, command=_on_confirm, width=125)
        btn_confirm.pack(side="right")

        # Setup keyboard navigation and hotkeys
        setup_form_keyboard_navigation(
            widgets=[btn_confirm, btn_cancel],
            on_submit=_on_confirm,
            on_cancel=self.destroy,
            toplevel=self,
        )
        btn_confirm.bind("<Return>", lambda _e: (_on_confirm(), "break")[1])
        btn_confirm.bind("<space>", lambda _e: (_on_confirm(), "break")[1])
        btn_cancel.bind("<Return>", lambda _e: (self.destroy(), "break")[1])
        btn_cancel.bind("<space>", lambda _e: (self.destroy(), "break")[1])

        self._focus_after_id = self.after(50, btn_cancel.focus_set)

    def destroy(self):
        try:
            if hasattr(self, "_focus_after_id") and self._focus_after_id:
                self.after_cancel(self._focus_after_id)
        except Exception:
            pass
        super().destroy()


def setup_form_keyboard_navigation(
    widgets: list[Any],
    on_submit: Optional[Callable[[], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None,
    toplevel: Optional[Any] = None,
) -> None:
    """Configure robust, circular Tab/Shift-Tab traversal and Enter/Escape hotkeys.

    Args:
        widgets: Ordered list of interactive widgets to cycle through with Tab / Shift-Tab.
        on_submit: Optional callback executed when Enter is pressed in text fields or on the submit button.
        on_cancel: Optional callback executed when Escape is pressed or on the cancel button.
        toplevel: Optional toplevel window to bind global Escape key.
    """
    if not widgets:
        return

    def focus_widget(w: Any) -> None:
        if hasattr(w, "entry"):
            w.entry.focus_set()
        elif hasattr(w, "focus_set"):
            w.focus_set()
        elif hasattr(w, "focus"):
            w.focus()

    for i, w in enumerate(widgets):
        nxt = widgets[(i + 1) % len(widgets)]
        prv = widgets[(i - 1) % len(widgets)]

        def make_tab(target):
            def _tab_handler(_e=None):
                focus_widget(target)
                return "break"
            return _tab_handler

        def make_shift_tab(target):
            def _shift_tab_handler(_e=None):
                focus_widget(target)
                return "break"
            return _shift_tab_handler

        tab_fn = make_tab(nxt)
        shift_tab_fn = make_shift_tab(prv)

        w._nav_next_widget = nxt
        w._nav_prev_widget = prv
        w._trigger_nav_next = tab_fn
        w._trigger_nav_prev = shift_tab_fn

        bind_targets = []
        if hasattr(w, "entry"):
            bind_targets.extend([w.entry, getattr(w.entry, "_entry", None)])
        else:
            bind_targets.extend([w, getattr(w, "_canvas", None), getattr(w, "_text_label", None)])

        for bt in bind_targets:
            if bt:
                bt.bind("<Tab>", tab_fn)
                bt.bind("<Shift-Tab>", shift_tab_fn)

        # Enter key behavior for entry fields:
        if on_submit and (hasattr(w, "entry") or isinstance(w, ctk.CTkEntry)):
            entry_target = w.entry if hasattr(w, "entry") else w
            def make_enter_handler(sub_fn):
                def _enter_handler(_e=None):
                    sub_fn()
                    return "break"
                return _enter_handler
            enter_fn = make_enter_handler(on_submit)
            w._trigger_nav_submit = enter_fn
            entry_target.bind("<Return>", enter_fn)

    # Escape key on modal toplevel
    if toplevel and on_cancel:
        def make_esc_handler(cancel_fn):
            def _esc_handler(_e=None):
                cancel_fn()
                return "break"
            return _esc_handler
        esc_fn = make_esc_handler(on_cancel)
        toplevel._trigger_nav_cancel = esc_fn
        toplevel.bind("<Escape>", esc_fn)

