"""Keyboard shortcuts configuration, validation, and persistence layer.

Provides custom keyboard shortcuts management saved with user data in SQLite:
- Default shortcuts:
    Ctrl+N: Add new item
    Ctrl+S: Quickly search item
    Ctrl+L: Filter / sort to low stock
    Ctrl+D: Go to Dashboard
    Ctrl+I: Go to Inventory
    Ctrl+P: Go to Settings
    Ctrl+R: Refresh active view
- Normalization, validation against reserved keys, and Tkinter sequence generation.
- Persistence in app_settings table under 'shortcuts'.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from app.database.queries import execute_update_or_delete, fetch_one

logger = logging.getLogger(__name__)

# Action identifiers
ACTION_ADD_ITEM = "add_item"
ACTION_QUICK_SEARCH = "quick_search"
ACTION_FILTER_LOW_STOCK = "filter_low_stock"
ACTION_NAV_DASHBOARD = "nav_dashboard"
ACTION_NAV_INVENTORY = "nav_inventory"
ACTION_NAV_SETTINGS = "nav_settings"
ACTION_REFRESH = "refresh_data"

# Default shortcut mappings requested by user specification
DEFAULT_SHORTCUTS: Dict[str, str] = {
    ACTION_ADD_ITEM: "Ctrl+N",
    ACTION_QUICK_SEARCH: "Ctrl+S",
    ACTION_FILTER_LOW_STOCK: "Ctrl+L",
    ACTION_NAV_DASHBOARD: "Ctrl+D",
    ACTION_NAV_INVENTORY: "Ctrl+I",
    ACTION_NAV_SETTINGS: "Ctrl+P",
    ACTION_REFRESH: "Ctrl+R",
}

SHORTCUT_METADATA: Dict[str, Dict[str, str]] = {
    ACTION_ADD_ITEM: {
        "name": "Add New Item",
        "description": "Open 'Add Product' dialog modal from anywhere",
        "default": "Ctrl+N",
        "icon": "➕",
    },
    ACTION_QUICK_SEARCH: {
        "name": "Quick Search Item",
        "description": "Instantly focus quick-search bar in Dashboard or Inventory",
        "default": "Ctrl+S",
        "icon": "🔎",
    },
    ACTION_FILTER_LOW_STOCK: {
        "name": "Filter / Sort Low Stock",
        "description": "Navigate to Inventory filtered and sorted by low stock alerts",
        "default": "Ctrl+L",
        "icon": "⚠️",
    },
    ACTION_NAV_DASHBOARD: {
        "name": "Go to Dashboard",
        "description": "Switch view to Store Analytics & Overview Dashboard",
        "default": "Ctrl+D",
        "icon": "📊",
    },
    ACTION_NAV_INVENTORY: {
        "name": "Go to Inventory",
        "description": "Switch view to Inventory Management Table",
        "default": "Ctrl+I",
        "icon": "📦",
    },
    ACTION_NAV_SETTINGS: {
        "name": "Go to Settings",
        "description": "Switch view to Application Settings & Preferences",
        "default": "Ctrl+P",
        "icon": "⚙️",
    },
    ACTION_REFRESH: {
        "name": "Refresh Active View",
        "description": "Reload inventory data, counters, and analytics",
        "default": "Ctrl+R",
        "icon": "🔄",
    },
}

# Standard text editing combinations that must not be overridden
RESERVED_COMBOS = {
    "CTRL+C",
    "CTRL+V",
    "CTRL+X",
    "CTRL+Z",
    "CTRL+A",
    "CTRL+Y",
}


def normalize_shortcut(raw_shortcut: str) -> str:
    """Normalize and validate a human-readable keyboard shortcut string.

    Examples:
        'ctrl + n' -> 'Ctrl+N'
        'ctrl+shift+s' -> 'Ctrl+Shift+S'
        'f5' -> 'F5'
        'alt+l' -> 'Alt+L'

    Raises:
        ValueError: If format is invalid, empty, or uses reserved system combinations.
    """
    if not raw_shortcut or not str(raw_shortcut).strip():
        raise ValueError("Shortcut key cannot be empty.")

    clean = str(raw_shortcut).strip().replace(" ", "")
    tokens = [t for t in re.split(r"\+", clean) if t]
    if not tokens:
        raise ValueError("Invalid shortcut format.")

    modifiers: List[str] = []
    key: Optional[str] = None

    for token in tokens:
        lower_token = token.lower()
        if lower_token in ("ctrl", "control"):
            if "Ctrl" not in modifiers:
                modifiers.append("Ctrl")
        elif lower_token == "alt":
            if "Alt" not in modifiers:
                modifiers.append("Alt")
        elif lower_token == "shift":
            if "Shift" not in modifiers:
                modifiers.append("Shift")
        else:
            if key is not None:
                raise ValueError(f"Multiple primary keys specified: '{key}' and '{token}'.")
            key = token

    if not key:
        raise ValueError(
            f"Shortcut '{raw_shortcut}' has modifiers but is missing a primary key (e.g. 'Ctrl+N')."
        )

    # Normalize key representation
    key_upper = key.upper()
    if re.match(r"^F(1[0-2]|[1-9])$", key_upper):
        normalized_key = key_upper
    elif len(key) == 1:
        normalized_key = key.upper() if key.isalpha() else key
    else:
        normalized_key = key.capitalize()

    # Disallow bare single letter without modifiers
    if not modifiers and len(normalized_key) == 1 and normalized_key.isalpha():
        raise ValueError(
            f"Shortcut '{normalized_key}' must include a modifier key (e.g. 'Ctrl+{normalized_key}' or 'Alt+{normalized_key}') to avoid interfering with normal text entry."
        )

    combo_parts = modifiers + [normalized_key]
    normalized_shortcut = "+".join(combo_parts)

    # Check for reserved keys
    if normalized_shortcut.upper() in RESERVED_COMBOS:
        raise ValueError(
            f"'{normalized_shortcut}' is reserved for standard text clipboard editing (Copy/Paste/Undo/Select All)."
        )

    return normalized_shortcut


def shortcut_to_tk_sequences(normalized_shortcut: str) -> List[str]:
    """Convert a normalized shortcut string (e.g. 'Ctrl+N') to Tkinter event sequences.

    Returns a list of equivalent Tk event sequences to handle both uppercase and
    lowercase key events across platforms.
    """
    tokens = normalized_shortcut.split("+")
    modifiers = tokens[:-1]
    key = tokens[-1]

    # Map modifiers to Tkinter syntax
    tk_mods: List[str] = []
    for mod in modifiers:
        if mod == "Ctrl":
            tk_mods.append("Control")
        elif mod == "Alt":
            tk_mods.append("Alt")
        elif mod == "Shift":
            tk_mods.append("Shift")
        else:
            tk_mods.append(mod)

    mod_prefix = "-".join(tk_mods)
    if mod_prefix:
        mod_prefix = mod_prefix + "-"

    sequences: List[str] = []

    if re.match(r"^F(1[0-2]|[1-9])$", key, re.IGNORECASE):
        # Function key
        fn_key = key.upper()
        if mod_prefix:
            sequences.append(f"<{mod_prefix}{fn_key}>")
        else:
            sequences.append(f"<{fn_key}>")
    elif len(key) == 1:
        if key.isalpha():
            # Add both lower and upper case variants
            k_lower = key.lower()
            k_upper = key.upper()
            if mod_prefix:
                sequences.append(f"<{mod_prefix}{k_lower}>")
                sequences.append(f"<{mod_prefix}{k_upper}>")
                sequences.append(f"<{mod_prefix}Key-{k_lower}>")
                sequences.append(f"<{mod_prefix}Key-{k_upper}>")
            else:
                sequences.append(f"<{k_lower}>")
                sequences.append(f"<{k_upper}>")
        else:
            if mod_prefix:
                sequences.append(f"<{mod_prefix}{key}>")
                sequences.append(f"<{mod_prefix}Key-{key}>")
            else:
                sequences.append(f"<{key}>")
    else:
        if mod_prefix:
            sequences.append(f"<{mod_prefix}{key}>")
        else:
            sequences.append(f"<{key}>")

    # Deduplicate preserving order
    seen = set()
    result = []
    for seq in sequences:
        if seq not in seen:
            seen.add(seq)
            result.append(seq)
    return result


class ShortcutManager:
    """Service layer for retrieving, updating, and persisting user keyboard shortcuts."""

    SETTINGS_KEY = "shortcuts"

    @staticmethod
    def get_shortcuts(custom_path: Optional[Union[str, Path]] = None) -> Dict[str, str]:
        """Fetch configured shortcuts from SQLite app_settings.

        Falls back to DEFAULT_SHORTCUTS for any missing or unconfigured actions.
        """
        shortcuts = dict(DEFAULT_SHORTCUTS)
        try:
            row = fetch_one(
                "SELECT value FROM app_settings WHERE key = ?;",
                (ShortcutManager.SETTINGS_KEY,),
                custom_path=custom_path,
            )
            if row and row["value"]:
                parsed = json.loads(row["value"])
                if isinstance(parsed, dict):
                    for action, sc in parsed.items():
                        if action in DEFAULT_SHORTCUTS and isinstance(sc, str):
                            try:
                                shortcuts[action] = normalize_shortcut(sc)
                            except ValueError:
                                pass
        except Exception as exc:
            logger.warning("Could not read shortcuts preference from database: %s", exc)

        return shortcuts

    @staticmethod
    def save_shortcuts(
        new_shortcuts: Dict[str, str],
        custom_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, str]:
        """Validate and persist customized keyboard shortcuts in app_settings.

        Raises:
            ValueError: If any shortcut is invalid or conflicts with reserved keys.
        """
        validated: Dict[str, str] = {}
        for action in DEFAULT_SHORTCUTS:
            if action in new_shortcuts:
                raw_val = new_shortcuts[action]
                normalized = normalize_shortcut(raw_val)
                validated[action] = normalized
            else:
                validated[action] = DEFAULT_SHORTCUTS[action]

        # Verify no duplicate assignments among configured actions
        reversed_map: Dict[str, str] = {}
        for action, sc in validated.items():
            if sc in reversed_map:
                act_a = SHORTCUT_METADATA[reversed_map[sc]]["name"]
                act_b = SHORTCUT_METADATA[action]["name"]
                raise ValueError(
                    f"Conflict detected: Shortcut '{sc}' is assigned to both '{act_a}' and '{act_b}'."
                )
            reversed_map[sc] = action

        payload = json.dumps(validated)
        execute_update_or_delete(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
            """,
            (ShortcutManager.SETTINGS_KEY, payload),
            custom_path=custom_path,
        )
        logger.info("Persisted custom shortcuts in database: %s", validated)
        return validated

    @staticmethod
    def reset_shortcuts_to_defaults(
        custom_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, str]:
        """Reset all shortcuts to default mappings and persist in database."""
        return ShortcutManager.save_shortcuts(DEFAULT_SHORTCUTS, custom_path=custom_path)
