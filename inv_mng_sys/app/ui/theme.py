"""Visual styling, color palette, and typography system for CustomTkinter UI.

Design Principles:
- Follows CustomTkinter color tuple format: (light_mode_color, dark_mode_color).
- Restrained, professional desktop aesthetic optimized for inventory management.
- High contrast, legible typography hierarchy based on Segoe UI.
- Consistent semantic colors for product stock statuses and operational states.
"""

# Semantic Color Palette: (light_mode_color, dark_mode_color)
COLOR_PRIMARY = ("#2563eb", "#3b82f6")
COLOR_PRIMARY_HOVER = ("#1d4ed8", "#2563eb")
COLOR_SECONDARY = ("#f1f5f9", "#334155")
COLOR_SECONDARY_HOVER = ("#e2e8f0", "#475569")
COLOR_SUCCESS = ("#16a34a", "#22c55e")
COLOR_SUCCESS_HOVER = ("#15803d", "#16a34a")
COLOR_WARNING = ("#d97706", "#f59e0b")
COLOR_DANGER = ("#dc2626", "#ef4444")
COLOR_DANGER_HOVER = ("#b91c1c", "#dc2626")
COLOR_INFO = ("#0284c7", "#38bdf8")

# Surface & Container Colors
COLOR_SURFACE_BG = ("#f8fafc", "#0f172a")
COLOR_CARD_BG = ("#ffffff", "#1e293b")
COLOR_CARD_HOVER = ("#f8fafc", "#243248")
COLOR_INPUT_BG = ("#ffffff", "#1e293b")
COLOR_BORDER = ("#e2e8f0", "#334155")
COLOR_BORDER_FOCUS = ("#93c5fd", "#60a5fa")
COLOR_TABLE_HEADER = ("#f1f5f9", "#111827")
COLOR_ROW_ALT = ("#f8fafc", "#172033")
COLOR_ROW_HOVER = ("#f1f5f9", "#243248")

# Typography Colors
COLOR_TEXT_PRIMARY = ("#0f172a", "#f8fafc")
COLOR_TEXT_MUTED = ("#64748b", "#94a3b8")
COLOR_TEXT_LIGHT = ("#94a3b8", "#64748b")
COLOR_TEXT_ERROR = ("#dc2626", "#f87171")
COLOR_TEXT_ON_PRIMARY = "#ffffff"

# Typography Scale (Font Family, Size, Weight)
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 13, "normal")
FONT_HEADING = (FONT_FAMILY, 16, "bold")
FONT_SECTION = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 12, "normal")
FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
FONT_SMALL = (FONT_FAMILY, 11, "normal")
FONT_BUTTON = (FONT_FAMILY, 12, "bold")
FONT_STAT_VALUE = (FONT_FAMILY, 26, "bold")
FONT_STAT_TITLE = (FONT_FAMILY, 11, "bold")
FONT_TABLE_HEADER = (FONT_FAMILY, 11, "bold")

# Dimension & Spacing Constants
RADIUS_CARD = 8
RADIUS_BUTTON = 6
RADIUS_INPUT = 6
RADIUS_BADGE = 10
RADIUS_MODAL = 10

HEIGHT_INPUT = 36
HEIGHT_BUTTON_LG = 36
HEIGHT_BUTTON_MD = 32
HEIGHT_BUTTON_SM = 28
HEIGHT_TABLE_ROW = 42
HEIGHT_HEADER = 36
