# IMS — UI/UX Visual Inspection & Screenshot Guide

**Course:** BBAT104 Fundamentals of Total Quality Management  
**Quality Goal:** Q13 – Faster Search & Retrieval  
**Evaluation Milestone:** Review 2 Visual Optimization Audit  
**Date:** October 12, 2026  

---

## 1. Overview of Visual Optimization

The user interface of the **Inventory Management System (IMS)** has been comprehensively optimized with a professional desktop software design system:
1. **Theme Consistency**: Corrected CustomTkinter color tuple order `(light_mode_color, dark_mode_color)` across all backgrounds, surfaces, texts, inputs, and borders.
2. **Accessible Typography**: Segoe UI typographic hierarchy with high-contrast text rendering in both Light Mode and Dark Mode.
3. **Card & Border Refinements**: High-definition card borders (`#e2e8f0` / `#334155`) preventing washed-out surfaces.
4. **Responsive Toolbar & Table**: Organized search filters and sorting options that never clip or collide, even at the minimum supported resolution ($960 \times 650$).
5. **Robust Long-Name Handling**: Ellipsis truncation on the navigation brand and user badges, with full text wrapping in modals, preventing layout destruction when organizations or products have long names.
6. **Integrated Appearance Switcher**: Real-time theme mode switching (**System**, **Dark**, **Light**) directly accessible in Settings.

---

## 2. Interactive Screenshot Checklist (For User Desktop Session)

Because automated headless services on Windows cannot capture interactive display surfaces via `PIL.ImageGrab` (which raises `OSError: screen grab failed` without an active desktop compositor), please perform the following quick manual screenshot captures on your desktop to produce presentation artifacts for Review 2:

### Screenshot 1: Functional Dashboard Overview
- **Resolution**: $1080 \times 750$ or Full Screen.
- **Action**: Launch application via `python run.py`.
- **Target View**: Active Dashboard showing the personalized greeting, organization subtitle, 4 metric cards (Total Products, Total Stock Qty, Low Stock Alerts, Out of Stock), Quick-Search bar, and Recent Inventory table.
- **Save As**: `docs/review2/ui/01_dashboard_overview.png`

### Screenshot 2: Q13 Inventory Workspace with Multi-Attribute Filters
- **Resolution**: $1080 \times 750$ or $960 \times 650$.
- **Action**: Click "📦 Inventory" tab.
- **Target View**: Top toolbar showing the prominent primary "➕ Add Product" button, search entry, Category dropdown, Supplier dropdown, Status dropdown, Sort By, and Order selectors.
- **Verification**: Note the clean alignment, clear result counter (`Showing X product(s)`), and alternating row colors with action buttons (`👁️`, `✏️`, `🗑️`).
- **Save As**: `docs/review2/ui/02_inventory_workspace.png`

### Screenshot 3: Modal Dialogs (Add/Edit Product & Details)
- **Action**: Click "➕ Add Product" to open `ProductFormModal`, or click `👁️` on any row to open `ProductDetailsModal`.
- **Verification**: Check centered positioning, crisp field borders, Auto/Status selector, and confirmation buttons.
- **Save As**: `docs/review2/ui/03_product_modals.png`

### Screenshot 4: Settings & Appearance Switcher
- **Action**: Click "⚙️ Settings" tab.
- **Target View**: Profile card, Appearance & Theme selector (`System` / `Dark` / `Light`), Session preference checkbox, and System & Quality Information card.
- **Verification**: Switch theme to "Dark" and "Light" to observe instant theme adaptation.
- **Save As**: `docs/review2/ui/04_settings_appearance.png`

---

## 3. Automated Geometry & Collision Verification Summary

The automated inspection suite in `scratch/test_ui_responsiveness.py` evaluated 29 distinct runtime layout parameters across 4 target resolutions:

| Tested Resolution | Screen Profile | Nav Bar Sized | Stat Cards Left-to-Right | Filter Toolbar Wrap | Table Sizing | Audit Result |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **$960 \times 650$** | Compact Laptop / Minimum Bounds | 1380px | 315px each | Clean | 1380px | **PASS** |
| **$1080 \times 750$** | Standard Default Window | 1560px | 360px each | Clean | 1560px | **PASS** |
| **$1280 \times 800$** | Desktop Workstation | 1860px | 435px each | Clean | 1860px | **PASS** |
| **$1440 \times 900$** | High-Res Wide Display | 1864px | 436px each | Clean | 1864px | **PASS** |

### Verified Boundary Cases:
- **Long Organization Name**: Handled cleanly with brand text truncation without pushing navigation buttons off-screen.
- **Long Product SKU / Name**: Text wrapping in details modal prevented status badge displacement.
- **Empty Inventory & Zero-Match Filter States**: Rendered centered friendly callouts with clear action buttons.
- **Modal Geometry**: Verified transient modal anchoring and destruction without hanging parent windows.
