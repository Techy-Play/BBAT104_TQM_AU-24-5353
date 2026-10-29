# Inventory Management System (IMS)

A desktop-based Inventory Management System developed as part of the **BBAT104 – Fundamentals of Total Quality Management (TQM)** course project.

## Project Information

| Item | Details |
|---|---|
| **Course** | BBAT104 – Fundamentals of Total Quality Management |
| **System** | Inventory Management System (IMS) |
| **Academic Session** | 2026–27 |
| **Student Name** | Lokesh Paneru |
| **Roll Number** | 2410303003 |
| **Section** | C |
| **Assigned Quality Goal** | Q13 – Faster Search & Retrieval |
| **Platform** | Windows Desktop (10 / 11) |
| **Architecture** | 100% Offline Desktop Application (Zero Cloud / REST Dependencies) |
| **Intended User** | One local user: store or warehouse owner / manager |

---

## Target User Definition

* **One local user: store or warehouse owner / manager**

The application is specifically designed for a single store, shop, warehouse, or small-business owner or inventory manager operating locally on a standalone desktop computer or dedicated workstation terminal. 

The owner/manager maintains complete operational authority over the system:
- Managing physical products, stock levels, suppliers, and pricing directly.
- Tracking critical threshold stock levels (in-stock, low-stock alerts at $\le 10$, and out-of-stock items at $0$).
- Performing high-speed search and retrieval queries during daily warehouse/retail operations (**Q13 quality objective**).
- Maintaining local credential security without requiring network connectivity, multi-tenant complexity, or external IT assistance.
- Retaining complete data ownership, with options to preserve or reset data during reinstallation or through an authenticated in-app reset.

---

## Project Objective & Quality Focus (Q13)

The system provides a reliable, secure, and fast offline solution for managing inventory records, including adding, updating, deleting, searching, filtering, and sorting products.

The project rigorously applies TQM principles to achieve software quality, data integrity, usability, and measurable retrieval performance under the assigned quality goal:

> **Q13 — Faster Search & Retrieval**

---

## Five Implemented Feature Areas (Q13 Quality Scope)

The official BBAT104 Quality Goal table for Q13 suggests four feature entries: *Search Filters, Sorting Options, Dashboard Quick-Search, and Database Query Optimization*. However, the course project guidelines simultaneously require students to implement five distinct feature areas. 

In our implementation, **Dashboard** and **Dashboard Quick-Search** serve fundamentally different functional and operational purposes:
- The **Dashboard** acts as an operational monitoring cockpit providing real-time inventory statistics, valuation metrics, visual threshold indicators, and interactive deep links.
- The **Dashboard Quick-Search** acts as a high-speed multi-attribute retrieval bar across Product ID, Name, Category, and Supplier.

To satisfy the five-feature requirement while remaining strictly faithful to the actual codebase, the project documents and implements the following **five feature areas**:

### 1. Dashboard (Inventory Overview & Real-Time Statistics)
* **Purpose & Functionality**: A central operational command center (`app/dashboard/dashboard.py`) computing real-time inventory metrics directly through SQLite aggregate queries (`COUNT(*)`, `SUM(quantity)`, `SUM(quantity * price)`, low-stock count, and out-of-stock count).
* **Interactive Deep Links**: Metric cards ("Total Products", "Total Items in Stock", "Low Stock", "Out of Stock") feature interactive deep-link navigation pills (e.g., clicking *"View Low Stock ↗"* immediately transitions to the Inventory view with the Stock Status filter pre-configured to *"Low Stock"*).
* **Recent Overview Table**: Displays the top 15 recently modified inventory items with formatted SKU, Name, Category, Supplier, Quantity, Price, and Stock Status badges, alongside quick-action *"View"* and *"Open in Inventory ↗"* shortcuts.
* **Quality Benefit**: Provides instant operational visibility into stockouts, low-stock warnings, and total inventory capital valuation with zero manual calculation overhead.

### 2. Dashboard Quick-Search
* **Purpose & Functionality**: A dedicated, prominent quick-search bar (`app/inventory/search.py`) embedded on the dashboard enabling instantaneous product lookups.
* **Multi-Attribute Search**: Simultaneously queries across four fields in a single execution:
  - Product ID / SKU (`product_id`)
  - Product Name (`name`)
  - Category (`category`)
  - Supplier (`supplier`)
* **Rapid Interaction**: Triggers on `Return` keypress or clicking *"Search"*. A single-click *"Reset"* button restores the recent inventory overview in 0 ms. An *"Open in Inventory ↗"* button carries the query into the full inventory workspace.
* **Quality Benefit**: Reduces item retrieval time from multi-step navigation to a single search keystroke, directly fulfilling the Q13 objective.

### 3. Search Filters
* **Purpose & Functionality**: A composable multi-attribute filtering toolbar (`app/inventory/filters.py`) in the full inventory management workspace.
* **Supported Filter Dimensions**:
  - **Category Filter**: Case-insensitive exact match dropdown populated dynamically from SQLite distinct values via `get_distinct_categories()`.
  - **Supplier Filter**: Case-insensitive exact match dropdown populated dynamically via `get_distinct_suppliers()`.
  - **Stock Status Filter**: Filter by `"In Stock"`, `"Low Stock"` ($\le 10$), or `"Out of Stock"` ($0$).
  - **Text Query Filter**: Substring search across SKU, Name, Category, and Supplier.
  - **Numeric Range Filters**: Optional criteria for minimum/maximum quantity and minimum/maximum price.
* **Conjunctive (`AND`) Logic**: All active filters combine logically (e.g., Category = *"Tools"* `AND` Stock Status = *"Low Stock"*). A single-click *"Clear All Filters"* button restores the complete product catalog.
* **Quality Benefit**: Allows store managers to rapidly isolate specific sub-inventories without pagination delay or cognitive overload.

### 4. Sorting Options
* **Purpose & Functionality**: A secure, whitelisted sorting mechanism (`app/inventory/sorting.py`) for inventory tables.
* **Supported Sort Columns**:
  - Product ID (`product_id`)
  - Product Name (`name`)
  - Category (`category`)
  - Supplier (`supplier`)
  - Quantity (`quantity`)
  - Price (`price`)
  - Stock Status (`stock_status`)
  - Last Updated (`updated_at`)
  - Created Date (`created_at`)
* **Supported Directions**: Ascending (`ASC`) and Descending (`DESC`).
* **Security & Reliability**: Strictly validates columns and directions against an internal whitelist before query construction, eliminating SQL injection risks. Includes secondary ordering by primary key (`id`) for deterministic row sequences.
* **Quality Benefit**: Enables instant prioritization of inventory by price, volume, stock status, or modification date.

### 5. Database Query Optimization & Performance Benchmarking
* **Purpose & Functionality**: Architectural query tuning and indexing in SQLite (`app/database/schema.py`, `app/database/queries.py`):
  - **SQLite PRAGMAs**: Enables Write-Ahead Logging (`PRAGMA journal_mode = WAL;`), foreign key enforcement (`PRAGMA foreign_keys = ON;`), crash-safe synchronous mode (`PRAGMA synchronous = NORMAL;`), and lock timeout (`PRAGMA busy_timeout = 5000;`).
  - **Strategic B-Tree Indexes**:
    - `idx_products_product_id` (Unique point lookups in $< 0.035$ ms)
    - `idx_products_name` (Prefix searches and case-insensitive alphabetical sorting)
    - `idx_products_category` (Dropdown population and category filtering)
    - `idx_products_supplier` (Dropdown population and supplier filtering)
    - `idx_products_stock_status` (Instant status filtering)
    - `idx_products_cat_sup` (Composite index providing up to **3.74x measured speedup** on multi-attribute queries)
    - `idx_users_username` (Point lookups during authentication)
  - **Parameterized SQL**: 100% parameterized queries across all database operations.
  - **Query Plan Verification**: Analyzed via `EXPLAIN QUERY PLAN`. Distinguishes index-accelerated queries (`SEARCH USING INDEX`) from arbitrary substring queries (`LIKE '%term%'`) that appropriately execute full table scans (`SCAN TABLE`).
  - **Repeatable Benchmark Suite**: Standalone automated benchmark script (`run_benchmark.py`) testing isolated datasets of 1,000, 10,000, and 50,000 synthetic products.
* **Quality Benefit**: Delivers sub-10 ms query responsiveness across a 50,000-product catalog on standard offline desktop hardware.

---

## Additional System Capabilities

- 🔐 **Local User Authentication**: First-run account provisioning and password login using salted PBKDF2 (SHA-256) password hashing with 100,000 iterations.
- 👤 **User & Business Profile**: Personalized greetings and business identity management with persistent "Keep Me Logged In" configuration.
- 📦 **Inventory CRUD Operations**: Add, inspect, modify, and delete inventory items with custom threshold alerts (`low_stock_threshold`), automatic valuation, and status classification.
- 📊 **Shop Owner Inventory & Capital Analysis**: Shop owner dashboard featuring total stock valuation, KPI averages, stock health ratios, category capital allocation bars with deep links, and replenishment urgency alerts.
- 💱 **Currency Selection & Dynamic Price Conversion**: Dual currency preference (`Rupees (₹)` and `USD ($)`). Dynamically converts all product prices and valuations in SQLite using the standard exchange rate ($1\text{ USD} = 83\text{ INR}$), with immediate view updates.
- ⌨️ **Global Keyboard Shortcuts & Customization**:
  - `Ctrl+N`: Add New Item (opens Product Form modal from anywhere in the application).
  - `Ctrl+S`: Quickly Search Item (instantly focuses quick-search input field).
  - `Ctrl+L`: Sort / Filter to Low Stock items (navigates to Inventory sorted and filtered by low-stock alerts).
  - `Ctrl+D`: Go to Dashboard.
  - `Ctrl+I`: Go to Inventory.
  - `Ctrl+P`: Go to Settings.
  - `Ctrl+R`: Refresh Active View.
- ⚙️ **Configurable "Shortcuts" Section in Settings**: Dedicated Settings card allowing users to customize, update, and validate all shortcut key combinations. Custom shortcuts persist alongside user data in SQLite (`app_settings`), with a one-click "Reset to Defaults" option.
- 🗄️ **Persistent SQLite Database**: Persistent local database in `inv_mng_sys/database/ims.db` with transactional integrity and automatic rollback on failure.
- ⚠️ **Danger Zone (Account Deletion & Database Reset)**: Password-protected user account deletion that wipes all products, users, and sessions, cleanly restarting the application into the onboarding wizard.
- ⌨️ **Form Keyboard Navigation**: Full `Tab` / `Shift+Tab` cyclic traversal, `Enter` submission, and `Esc` dismissal across all inputs and dialogs.
- 🖥️ **Single-View Non-Scrolling UI**: Compact, balanced 2-column layouts for Add/Edit product modals, specifications cards, and the First-Run Setup wizard on scaled displays (100%, 125%, 150%).
- ⚡ **Flicker-Free Transitions**: Non-destructive view caching and pooled table row recycling eliminating screen flashing and widget redraw stutter.
- 🌓 **Theme Customization**: Real-time switching between System Default (Device Appearance), Dark Mode, and Light Mode with persistent storage.
- 🚀 **Windows Standalone Installer (`setup.exe`) & Uninstaller**: One-click Inno Setup 6 installer with desktop shortcuts, bundled icons, and data preservation prompts on reinstall and uninstall.

---

## System Architecture

The application follows a modular, layered desktop architecture:

1. **Presentation Layer** – CustomTkinter responsive GUI (Dashboard, Inventory views, Modals, Settings, Auth).
2. **Application Logic Layer** – Authentication, CRUD, search, filtering, sorting, and validation services.
3. **Quality & Optimization Layer** – Query optimization, indexing, and retrieval performance measurement.
4. **Data Layer** – Local SQLite database with WAL journaling, B-tree indexes, and PRAGMA integrity checks.

### Architecture Diagram

![IMS System Architecture](images/IMS_System_Architecture.png)

---

## Authentication Flow

The application supports a first-time setup process for creating the local user account. On subsequent launches, the user logs in using their password. The **Keep Me Logged In** option can also be controlled through application settings.

### Authentication Flow Diagram

![IMS Authentication Flow](images/IMS_Authentication_Flow.png)

---

## Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.11.x** | Core programming language (tested on Python 3.11.9) |
| **CustomTkinter 6.0** | Modern themeable desktop GUI |
| **SQLite3** | Local persistent embedded database with WAL mode |
| **Pandas** | Tabular data processing and analysis |
| **Matplotlib / Seaborn** | TQM/SQC quality charts and metrics |
| **PyInstaller & Inno Setup 6** | Standalone packaging and Windows installer (`setup.exe`) |
| **Git & GitHub** | Version control and academic deliverables |

---

## Installation & Execution

### Option 1: Standalone Windows Installer (Recommended for Users)
1. Download or locate `setup.exe` in the `inv_mng_sys/` folder.
2. Double-click `setup.exe` and follow the setup wizard.
3. Choose whether to create a Desktop Shortcut (official icon included).
4. If an existing database is detected from an earlier install, the installer asks whether to **KEEP** existing data or perform a **FRESH START**.
5. Launch the application directly from the Start Menu or Desktop.

### Option 2: Running from Source (Development Environment)

1. **Clone the repository**:
   ```powershell
   git clone https://github.com/Techy-Play/BBAT104_TQM_AU-24-5353.git
   cd "BBAT104_TQM_AU-24-5353/inv_mng_sys"
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```powershell
   python run.py
   ```

5. **Run the automated test suite**:
   ```powershell
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

6. **Run the Q13 performance benchmark suite**:
   ```powershell
   python run_benchmark.py
   ```

---

## Project Structure

```text
TQM Project/
│
├── README.md                          # Comprehensive project overview and instructions
├── SRS.md                             # Software Requirements Specification (BBAT104)
│
├── images/
│   ├── IMS_Authentication_Flow.png   # Flowchart for onboarding and login
│   └── IMS_System_Architecture.png    # Layered architecture diagram
│
└── inv_mng_sys/                       # Source code directory
    ├── app/
    │   ├── main.py                    # Application coordinator, hotkey dispatching, window manager
    │   ├── database/                  # Connection layer, schema, indexes, queries
    │   ├── authentication/            # Security, PBKDF2 hashing, setup, login
    │   ├── inventory/                 # CRUD logic, filters, sorting, search, benchmark
    │   ├── dashboard/                 # Real-time statistics, deep links, quick-search, analytics
    │   ├── settings/                  # User profile, theme, currency conversion, shortcuts service
    │   └── ui/                        # CustomTkinter theme, components, views, dialogs
    │
    ├── database/                      # Persistent SQLite storage (ims.db)
    ├── tests/                         # 70 automated unittest test cases (9 suites)
    ├── docs/                          # Architecture, database design, review checklists
    ├── app_icon.ico                   # Multi-resolution Windows application icon
    ├── app_icon.png                   # High-resolution PNG application icon
    ├── build_installer.py             # Packaging and Inno Setup automation script
    ├── ims.spec                       # PyInstaller packaging specification
    ├── installer.iss                  # Inno Setup 6 installer configuration
    ├── setup.exe                      # Standalone Windows installer (22.09 MB)
    ├── requirements.txt               # Python package dependencies
    ├── run_benchmark.py               # Q13 query performance benchmark script
    └── run.py                         # Application bootstrap entry point
```

---

## TQM Quality Practices & Course Deliverables

The project applies software quality practices aligned with TQM methodologies:
- **Quality Goal Traceability**: Clear mapping from Q13 objective down to database indexes and UI controls.
- **Defect Prevention**: Parameterized queries, whitelisted sorting, and validation checks preventing data corruption.
- **Empirical Quality Evidence**: Repeatable benchmarks and `EXPLAIN QUERY PLAN` logs verifying retrieval speedup.
- **Robustness**: 100% automated test pass rate across 70 test cases.

---

## Project Status

- **Review 1**: Completed (Project conceptualization, SRS, and initial architecture).
- **Review 2**: Completed & Verified (Authentication, Dashboard, Inventory CRUD, Q13 Search & Retrieval, Standalone Installer Packaging, 70 automated tests).

---

## Academic License & Integrity

This project is developed for academic evaluation as part of the **BBAT104 – Fundamentals of Total Quality Management** course.
- **Student Name**: Lokesh Paneru
- **Roll Number**: 2410303003
- **Section**: C
