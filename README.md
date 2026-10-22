# Inventory Management System

A desktop-based Inventory Management System developed as part of the **BBAT104 – Fundamentals of Total Quality Management (TQM)** course project.

## Project Information

| Item | Details |
|---|---|
| **Course** | BBAT104 – Fundamentals of TQM |
| **System** | Inventory Management System (IMS) |
| **Quality Goal** | Q13 – Faster Search & Retrieval |
| **Platform** | Windows Desktop (10 / 11) |
| **Mode** | Fully Offline Desktop Application |
| **Developer** | Lokesh Paneru |
| **Intended User** | One local user: store or warehouse owner / manager |

---

## Target User Definition

* **One local user: store or warehouse owner / manager**

The application is specifically designed for a single store, shop, warehouse, or small-business owner or inventory manager operating locally on a standalone desktop computer or dedicated workstation terminal. 

The owner/manager maintains complete operational authority over the system:
- Managing products, stock levels, suppliers, and pricing directly.
- Tracking threshold stock levels (in-stock, low-stock alerts, and out-of-stock items).
- Performing high-speed search and retrieval queries during daily operations (Q13 quality objective).
- Maintaining local credential security without requiring network connectivity, multi-tenant complexity, or external IT assistance.

---

## Project Objective

The system provides a reliable, secure, and fast offline solution for managing inventory records, including adding, updating, deleting, searching, filtering, and sorting products.

The project rigorously applies TQM principles to achieve software quality, data integrity, usability, and measurable retrieval performance.

---

## Key Features

- 🔐 **Local User Authentication**: First-run account provisioning and password login using salted PBKDF2 (SHA-256) password hashing.
- 👤 **User & Business Profile**: Personalized greetings and business identity management with persistent "Keep Me Logged In" configuration.
- 📦 **Inventory CRUD Operations**: Add, inspect, modify, and delete inventory items with automatic total stock valuation and stock status calculation.
- 🔎 **Q13 Dashboard Quick-Search**: Instant search across Product SKU, Name, Category, and Supplier.
- 🔍 **Multi-Attribute Search Filters**: Simultaneous filtering by Category, Supplier, Stock Status, and free-text queries with one-click filter clearing.
- ↕️ **Whitelisted Sorting**: Secure ascending and descending sorting across all key inventory attributes.
- 🗄️ **Persistent SQLite Database**: Persistent local database with B-Tree indexes, WAL concurrency, and transactional foreign key integrity.
- ⚠️ **Danger Zone (Account Deletion & Database Reset)**: Password-protected user account deletion that wipes all products, users, and sessions, cleanly restarting the application into the onboarding wizard.
- ⌨️ **Keyboard Navigation & Hotkeys**: Full `Tab` / `Shift+Tab` cyclic traversal, `Enter` submission, and `Esc` dismissal across all inputs and dialogs.
- 🖥️ **Single-View Non-Scrolling UI**: Compact, balanced 2-column layouts for Add/Edit product modals, specifications cards, and the First-Run Setup wizard on scaled displays (100%, 125%, 150%).
- 🌓 **Theme Customization**: Real-time switching between System Default (Device Appearance), Dark Mode, and Light Mode with persistent storage.
- 🚀 **Windows Standalone Installer (`setup.exe`) & Uninstaller**: One-click installer with data preservation prompts on reinstall and uninstall.
- 📊 **Performance Benchmarking**: Integrated automated Q13 benchmark measuring indexed vs. unindexed search across 1,000 to 50,000 items.
- 💻 **100% Offline Desktop Application**: Runs completely disconnected from the Internet with zero cloud or REST API dependencies.

---

## System Architecture

The application follows a modular, layered desktop architecture:

1. **Presentation Layer** – CustomTkinter responsive GUI (Dashboard, Inventory views, Modals, Settings, Auth).
2. **Application Logic Layer** – Authentication, CRUD, search, filtering, sorting, and validation services.
3. **Quality & Optimization Layer** – Query optimization, indexing, and retrieval performance measurement.
4. **Data Layer** – Local SQLite database with WAL journaling and PRAGMA integrity checks.

### Architecture Diagram

![IMS System Architecture](images/IMS_System_Architecture.png)

---

## Authentication Flow

The application supports a first-time setup process for creating the local user account.

On subsequent launches, the user can log in using their password. The **Keep Me Logged In** option can also be controlled through application settings.

### Authentication Flow Diagram

![IMS Authentication Flow](images/IMS_Authentication_Flow.png)

---

## Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.11.x** | Core programming language |
| **CustomTkinter 6.0** | Modern themeable desktop GUI |
| **SQLite3** | Local persistent embedded database |
| **Pandas** | Tabular data processing and analysis |
| **Matplotlib / Seaborn** | TQM/SQC quality charts and metrics |
| **PyInstaller & Inno Setup 6** | Standalone packaging and Windows installer (`setup.exe`) |
| **Git & GitHub** | Version control and academic deliverables |

---

## Installation & Execution

### Option 1: Standalone Windows Installer (Recommended for Users)
1. Download or locate `setup.exe` in the `inv_mng_sys/` folder.
2. Double-click `setup.exe` and follow the setup wizard.
3. Choose whether to create a Desktop Shortcut.
4. If an existing database is detected from an earlier install, the installer will ask whether to **KEEP** existing data or perform a **FRESH START**.
5. Launch the application directly from the Start Menu or Desktop.

### Option 2: Running from Source (Development Environment)

1. **Clone the repository**:
   ```powershell
   git clone https://github.com/Techy-Play/BBAT104_TQM_AU-24-5353.git
   cd "TQM Project/inv_mng_sys"
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

6. **Run the Q13 performance benchmark**:
   ```powershell
   python run_benchmark.py
   ```

---

## Project Structure

```text
TQM Project/
│
├── README.md                          # Project overview and instructions
├── SRS.md                             # Software Requirements Specification
│
├── images/
│   ├── IMS_Authentication_Flow.png   # Flowchart for onboarding and login
│   └── IMS_System_Architecture.png    # Layered architecture diagram
│
└── inv_mng_sys/                       # Source code directory
    ├── app/
    │   ├── main.py                    # Application coordinator and window manager
    │   ├── database/                  # Connection layer, schema, indexes, queries
    │   ├── authentication/            # Security, PBKDF2 hashing, setup, login
    │   ├── inventory/                 # CRUD logic, filters, sorting, validation
    │   ├── dashboard/                 # Real-time statistics and quick-search
    │   ├── settings/                  # User profile, theme settings, account reset
    │   └── ui/                        # CustomTkinter theme, components, views, dialogs
    │
    ├── database/                      # Persistent SQLite storage (ims.db)
    ├── tests/                         # 51 automated unittest test cases
    ├── docs/                          # Architecture, database design, setup guides
    ├── app_icon.ico                   # Windows application icon
    ├── build_installer.py             # Packaging and Inno Setup automation script
    ├── ims.spec                       # PyInstaller packaging specification
    ├── installer.iss                  # Inno Setup 6 installer configuration
    ├── setup.exe                      # Standalone Windows installer (22 MB)
    ├── requirements.txt               # Python package dependencies
    ├── run_benchmark.py               # Q13 query performance benchmark script
    └── run.py                         # Application bootstrap entry point
```

---

## TQM Application & Quality Practices

The project applies software quality practices including:
- Requirements definition and traceability.
- Quality-focused feature development (Q13 Faster Search & Retrieval).
- Database indexing and query plan optimization.
- Systematic error handling and input validation.
- FMEA and risk analysis.
- Statistical Quality Control (SQC).
- Continuous improvement and defect logging.
- GitHub-based version control and documentation integrity.

---

## Project Status

- **Review 1**: Completed (Project conceptualization, SRS, and initial architecture).
- **Review 2**: Completed (Authentication, Dashboard, Inventory CRUD, Q13 Search & Retrieval, Packaging, 51 automated tests).

---

## License

This project is developed for academic purposes as part of the **BBAT104 – Fundamentals of Total Quality Management** course.
