# Environment Setup & Execution Instructions

## 1. Prerequisites

- **Python**: Python 3.11.x (tested on Python 3.11.9)
- **Operating System**: Windows 10/11 (fully offline compatible)
- **SQLite3**: Built into Python standard library (no external installation required)

---

## 2. Setting Up the Virtual Environment

Open a terminal (PowerShell or Command Prompt) and navigate to the project directory:

```powershell
cd "c:\Users\kamal\Documents\TQM Project\inv_mng_sys"
```

### Create the Virtual Environment:
```powershell
python -m venv .venv
```

### Activate the Virtual Environment:

- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(If execution policies restrict running scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your session)*

- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```

---

## 3. Install Dependencies

Once the virtual environment is activated, install the required packages:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Included Packages:
- `customtkinter`: Modern offline UI toolkit for Python.
- `pandas`: Data structures and dataset processing.
- `matplotlib` & `seaborn`: SQC and TQM charts for subsequent evaluation phases.
- `pytest`: Optional test discovery tool (Python standard library `unittest` is also supported out-of-the-box).

---

## 4. Running the Tests

To run the automated test suite covering database persistence, indexing, first-run setup, authentication, and session management:

```powershell
# Using Python's built-in unittest:
python -m unittest discover -s tests -p "test_*.py" -v

# Or using pytest:
pytest -v
```

---

## 5. Running the Q13 Performance Benchmark

To measure and verify query optimization across 1,000, 10,000, and 50,000 products:

```powershell
python run_benchmark.py
```
*(Executes isolated temporary database benchmarks comparing indexed vs. unindexed queries).*

---

## 6. Running the Application

To launch the desktop application:

```powershell
python run.py
# or
python app/main.py
```

---

## 7. Windows Standalone Installer (setup.exe)

The application includes an automated packaging pipeline that compiles the Python source into a standalone Windows installer (`setup.exe`).

### Installing via setup.exe:
Double-click `setup.exe` in the `inv_mng_sys/` directory. The installation wizard will:
1. Provide standard Windows installation prompts (defaults to per-user AppData or Program Files).
2. Offer an optional **Desktop Shortcut**.
3. Register a **Start Menu Shortcut** and official Windows **Uninstaller**.
4. Automatically persist local inventory databases at `%LOCALAPPDATA%\InventoryManagementSystem\database\ims.db` across re-installs and updates.

### Rebuilding the Installer:
To regenerate `setup.exe` from source:
```powershell
python build_installer.py
```
*(Requires `PyInstaller` and `Inno Setup 6`).*

---

## 8. Application Workflow & Launch Behavior

### First Launch (First-Run Setup)
When the application starts for the first time and detects an empty `users` table:
1. The **First-Run Setup** wizard is displayed.
2. The user configures:
   - Full Name
   - Store / Warehouse / Business Name
   - Unique Username
   - Password (minimum 6 characters) and Confirmation
   - "Keep Me Logged In" preference
3. Credentials are encrypted using salted PBKDF2 (SHA-256) and saved in `database/ims.db`.
4. The post-setup dashboard opens displaying personalized organization details.

### Subsequent Launches (Login & Sessions)
- **If Keep Me Logged In was enabled**: The application validates the cryptographic session token against the local database and enters directly into the dashboard.
- **If Keep Me Logged In was disabled**: The **Sign In** screen is displayed, prompting for username and password.
- **Log Out**: Clicking "Log Out" on the top navigation bar immediately clears the active session token in SQLite and returns the user to the login screen.

### Navigation & Core Views
- **Dashboard (`📊 Dashboard`)**: Displays personalized greetings, real-time aggregate statistics (Total Products, Total Stock Qty, Low Stock Alerts, Out of Stock), Quick-Search bar, and recent inventory table.
- **Inventory Management (`📦 Inventory`)**: Complete product management with search, "+ Add Product" modal, product details modal, edit modal, and delete confirmation dialogs.
- **Settings (`⚙️ Settings`)**: Allows updating user and organization identity, toggling Keep Me Logged In, and changing passwords.


---

## 7. Troubleshooting

- **Database Locked Error**: The database layer uses SQLite Write-Ahead Logging (`WAL` mode) and sets a 5000ms busy timeout. If a process locks the database, ensure only one instance is executing migrations.
- **PowerShell Script Execution Policy**: If `.venv\Scripts\Activate.ps1` gives an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your PowerShell terminal.
- **CustomTkinter Scaling**: CustomTkinter automatically scales based on Windows DPI settings. If running in a virtual machine or low-resolution display, ensure window minimum dimensions (860x620) can fit on screen.
