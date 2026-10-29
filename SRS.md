# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)

## Inventory Management System
### Quality Goal: Q13 — Faster Search & Retrieval

**Course:** BBAT104 — Fundamentals of Total Quality Management  
**Academic Session:** 2026–27  
**Student Name:** Lokesh Paneru  
**Roll Number:** 2410303003  
**Section:** C  
**Project Type:** Standalone Offline Desktop Application  
**Version:** 1.0  
**Technology:** Python 3.11.x, CustomTkinter 6.0, SQLite3  
**Primary Quality Objective:** Q13 — Faster Search & Retrieval  
**Target User:** One local user: store or warehouse owner / manager

---

# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional, non-functional, technical, and quality requirements of the **Inventory Management System** developed as part of the BBAT104 Fundamentals of TQM course project.

The system is an **offline desktop-based inventory management application** designed to allow a user to securely manage inventory data stored locally on the computer.

The primary quality objective of the system is **Faster Search & Retrieval (Q13)**. The system will therefore emphasize efficient database queries, quick-search functionality, search filters, and sorting mechanisms.

---

## 1.2 Project Objective

The main objective of the project is to develop a reliable and user-friendly inventory management application that allows users to:

- Create and manage an inventory database.
- Add, view, update, and delete inventory records.
- Quickly search for products.
- Filter inventory according to different attributes.
- Sort inventory records.
- Retrieve relevant records efficiently using optimized SQLite queries.
- Secure the application using a local user account and password.
- Operate completely without requiring an Internet connection.

The TQM quality goal assigned to this project is:

> **Q13 — Faster Search & Retrieval**

The official project guidelines associate Q13 with **Search Filters, Sorting Options, Dashboard Quick-Search, and Database Query Optimization** (four listed entries in the official quality table). However, the general course project guidelines simultaneously instruct students to implement five distinct feature areas.

In this implementation, **Dashboard** and **Dashboard Quick-Search** serve fundamentally different operational purposes:
- The **Dashboard** acts as an operational monitoring cockpit providing real-time inventory statistics, valuation metrics, visual threshold indicators (low-stock and out-of-stock), and interactive deep links.
- The **Dashboard Quick-Search** acts as a fast multi-attribute retrieval bar across Product ID, Name, Category, and Supplier.

Accordingly, the application documents and implements the following **five feature areas**:
1. **Dashboard:** Inventory overview, stock statistics, valuation, threshold indicators, and deep links.
2. **Dashboard Quick-Search:** High-speed product searching across Product ID, Name, Category, and Supplier.
3. **Search Filters:** Granular multi-attribute filtering by Category, Supplier, Stock Status, and text query.
4. **Sorting Options:** Strict whitelisted ascending and descending sorting across supported inventory attributes.
5. **Database Query Optimization:** SQLite B-tree indexes, WAL mode, parameterized queries, and empirical benchmark evaluation.

---

## 1.3 Target User Definition

* **One local user: store or warehouse owner / manager**

The system is explicitly designed for a single store, shop, warehouse, or small-business owner or inventory manager operating locally on a standalone personal computer or dedicated workstation terminal.

### User Characteristics & Operational Profile:
- **User Role**: Store Owner, Warehouse Supervisor, or Inventory Operations Manager.
- **Operational Context**: Directly oversees physical inventory items, stock levels, suppliers, and unit prices.
- **Key Operational Needs**:
  - Rapid search and retrieval of item details (SKU, quantity, category, supplier) during daily operations (Q13 goal).
  - Clear, immediate threshold alerts for low-stock (quantity <= 10) and out-of-stock items via dashboard metrics.
  - Complete operational independence in physical retail or warehouse environments without requiring cloud subscriptions or continuous internet access.
  - Straightforward, password-protected local authentication without complex multi-tenant administration.
  - Absolute control over local data retention, including preserving data across software updates or performing an authenticated reset.

---

# 2. Scope of the System

## 2.1 In-Scope

The following functionality is included within the scope of the project:

### User Authentication
- First-run account creation.
- Local username/account creation.
- Password creation.
- Password-based login.
- Keep Me Logged In option.
- Ability to change the Keep Me Logged In preference from Settings.
- Local authentication without Internet connectivity.
- User account deletion and database reset (Danger Zone) requiring current master password verification.

### Inventory Management
- Add new inventory items.
- View inventory items.
- Update existing inventory items.
- Delete inventory items.
- Store inventory information in SQLite.
- Maintain persistent data between application sessions.

### Q13 — Faster Search & Retrieval (Five Implemented Feature Areas)
- **1. Dashboard:** Real-time stock statistics, total valuation, low-stock/out-of-stock indicators, deep links, and recent inventory overview.
- **2. Dashboard Quick-Search:** Instant multi-attribute search across Product ID, Name, Category, and Supplier.
- **3. Search Filters:** Composable multi-dimensional filtering by Category, Supplier, Stock Status, and text query.
- **4. Sorting Options:** Whitelist-validated ascending and descending sorting across all key inventory attributes.
- **5. Database Query Optimization:** Strategic SQLite B-tree indexing, WAL concurrency, parameterized queries, and empirical benchmarking across 1,000, 10,000, and 50,000 products.

### Application
- Dashboard.
- Settings.
- Inventory management interface.
- Authentication interface.
- Error and validation messages.
- Local database management.
- Standalone Windows installer (setup.exe) and uninstaller with intelligent data preservation options.
- Single-view non-scrolling UI layouts and rapid keyboard navigation (Tab, Shift-Tab, Enter, Escape).

### TQM / Quality Analysis
The project will also support the documentation and analysis required by the TQM course, including:
- System architecture.
- SRS.
- Scope definition.
- FMEA.
- SIPOC.
- CTQ analysis.
- Defect logging.
- Pareto analysis.
- Fishbone analysis.
- PDCA cycle.
- Performance evaluation.

The official guidelines require these TQM/SQC activities as part of later project reviews. 

---

## 2.2 Out-of-Scope

The following functionality is intentionally excluded from the current project:

- Online/cloud synchronization.
- Online database.
- Internet-based authentication.
- Multi-computer inventory synchronization.
- Online user accounts.
- Online payment processing.
- E-commerce functionality.
- Remote inventory access.
- Cloud backup.
- Mobile application.
- Web application.
- External API integration.

The application is designed as a **standalone offline desktop application**.

---

# 3. Product Perspective

The Inventory Management System will operate as a standalone desktop application.

The overall architecture will be:

```text
┌──────────────────────────────────────┐
│       Inventory Management System    │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│        CustomTkinter GUI             │
│ Login │ Dashboard │ Inventory │      │
│ Search │ Filters │ Settings          │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│          Python Application Layer    │
│ Authentication │ CRUD │ Search       │
│ Filtering │ Sorting │ Validation     │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│              SQLite3                 │
│ Users │ Products │ Inventory Data    │
└──────────────────────────────────────┘
```

The application will not require an Internet connection for normal operation.

## 3.1 User Class & Operational Environment

The system is designed for:
* **One local user: store or warehouse owner / manager**

The operational environment is an offline personal computer running Microsoft Windows 10 or Windows 11. No network connection, background daemons, or remote database servers are utilized.

---

# 4. Technology Requirements

## 4.1 Programming Language

**Python 3.x**

Python will be used for:
- Application logic.
- Database interaction.
- Authentication.
- Search and filtering.
- Sorting.
- CRUD operations.
- Performance measurement.
- TQM/SQC chart generation.

The official guidelines specify Python 3.x as the core runtime. 

---

## 4.2 User Interface

**CustomTkinter**

CustomTkinter will be used to create the desktop graphical user interface.

The interface will contain:
- Login screen.
- Account creation screen.
- Dashboard.
- Inventory management screen.
- Search interface.
- Filter controls.
- Sorting controls.
- Settings screen.
- Notifications and validation messages.

The official guidelines allow Tkinter/CustomTkinter for GUI development. 

---

## 4.3 Database

**SQLite3**

SQLite3 will be used as the local database management system.

The database will store:
- User account information.
- Authentication-related information.
- Inventory records.
- Product information.
- Application preferences where appropriate.

The database must persist after application shutdown.

Every successful database modification must be committed using an appropriate transaction mechanism.

---

# 5. User Workflow

## 5.1 First Application Launch

When the application is launched for the first time:

```text
Application Launch
       ↓
Check Local Database
       ↓
Does User Account Exist?
       ↓
      NO
       ↓
Account Creation Screen
       ↓
Create Username + Password
       ↓
Save Account Locally
       ↓
Login / Dashboard
```

The system shall detect that no local user account exists and guide the user through account creation.

---

## 5.2 Subsequent Application Launch

When the application is opened after an account has already been created:

```text
Application Launch
       ↓
Check Authentication State
       ↓
Keep Me Logged In?
    ↙          ↘
   YES          NO
    ↓            ↓
 Dashboard    Login Screen
                 ↓
             Password
                 ↓
          Authentication
             ↙      ↘
          Correct   Incorrect
             ↓         ↓
        Dashboard   Error Message
```

If the Keep Me Logged In preference is enabled, the application may directly open the dashboard according to the locally stored authentication state.

If it is disabled, the application shall require the user to authenticate.

---

# 6. Functional Requirements

## FR-01 — First-Run Detection

The system shall determine whether a local user account has already been configured.

If no account exists, the system shall display the account creation interface.

---

## FR-02 — Account Creation

The system shall allow the user to create a local application account.

The account shall contain at minimum:
- Username.
- Password.

The system shall validate required fields before creating the account.

---

## FR-03 — User Profile Creation
During first-run setup, the system shall require the user to provide their name. The name shall be stored locally and used to personalize the application interface.

## FR-04 — Organization/Inventory Name
During first-run setup, the system shall ask the user to provide the name of the store, warehouse, business, or other entity for which the Inventory Management System is being used.
The application shall display this name in relevant areas of the dashboard.

## FR-05 — Profile Modification
The user shall be able to modify their name and Store/Warehouse/Business name from the application's Settings section.


## FR-06 — Personalized Dashboard
After successful authentication, the dashboard shall display the user's name and the configured Store/Warehouse/Business name where appropriate.

## FR-07 — Password Authentication

The system shall require authentication before granting access to protected application functionality.

The entered password shall be compared with the locally stored authentication information.

Incorrect authentication attempts shall result in an appropriate error message.

---

## FR-08 — Keep Me Logged In

The login screen shall provide a **Keep Me Logged In** option.

When enabled, the application shall remember the user's authentication state according to the application's local authentication mechanism.

When disabled, the application shall require authentication during subsequent launches.

---

## FR-09 — Authentication Preference Management

The Settings section shall allow the user to change the Keep Me Logged In preference.

The user shall not be required to reinstall or recreate the application account to change this preference.

---

# 7. Inventory Management Requirements

## FR-10 — Add Inventory Item

The system shall allow the user to create a new inventory record.

An inventory record should contain appropriate fields such as:

- Product ID
- Product Name
- Category
- Supplier
- Quantity
- Price
- Stock Status
- Date/Time of Update

The final database fields may be refined during database design.

---

## FR-11 — View Inventory

The system shall display stored inventory records in a structured table.

The user shall be able to view relevant inventory information without manually accessing the SQLite database.

---

## FR-12 — Update Inventory

The system shall allow authorized users to modify existing inventory records.

Changes shall be saved persistently to the SQLite database.

---

## FR-13 — Delete Inventory

The system shall allow the user to delete an inventory record.

The system should request confirmation before permanently deleting a record.

---

## FR-14 — Data Persistence

Inventory data shall remain available after:

- Closing the application.
- Restarting the application.
- Restarting the computer.

The application shall not recreate or reset the database during normal startup.

---

# 8. Q13 — Faster Search & Retrieval Requirements

This section represents the **core quality objective of the project**.

The official BBAT104 quality goal table lists four suggested feature entries for Q13 (*Search Filters, Sorting Options, Dashboard Quick-Search, and Database Query Optimization*). To satisfy the course requirement of five implemented features while reflecting the actual system implementation, the system treats **Dashboard Overview & Real-Time Stock Statistics** and **Dashboard Quick-Search** as two separate functional areas:
1. **Feature 1: Dashboard Overview & Real-Time Stock Statistics (FR-15)**
2. **Feature 2: Dashboard Quick-Search (FR-16)**
3. **Feature 3: Search Filters (FR-17)**
4. **Feature 4: Sorting Options (FR-18)**
5. **Feature 5: Database Query Optimization & Indexing (FR-19, FR-20)**

---

## FR-15 — Dashboard Overview & Real-Time Stock Statistics (Feature 1)

The system shall provide a dedicated dashboard view (`app/dashboard/dashboard.py`) serving as an operational monitoring center for inventory state.

### Capabilities & Specifications:
1. **Real-Time Aggregate Metrics**: The dashboard shall execute SQLite aggregate queries (`get_inventory_statistics()`) computing:
   - Total distinct products count (`COUNT(*)`).
   - Total physical items in stock (`COALESCE(SUM(quantity), 0)`).
   - Total inventory monetary valuation (`COALESCE(SUM(quantity * price), 0.0)`).
   - Low-stock items count (`SUM(CASE WHEN stock_status = 'Low Stock' THEN 1 ELSE 0 END)`), where quantity <= 10.
   - Out-of-stock items count (`SUM(CASE WHEN stock_status = 'Out of Stock' THEN 1 ELSE 0 END)`), where quantity == 0.
2. **Interactive Deep Links**:
   - Metric cards shall provide clickable deep-link buttons (e.g., *"View Low Stock ↗"*, *"View Out of Stock ↗"*).
   - Clicking a metric card link shall immediately transition to the full Inventory workspace with the corresponding stock status filter pre-selected and applied.
3. **Recent Inventory Overview**:
   - The dashboard shall display an overview table of the top 15 recently modified products.
   - For each item, the overview shall present Product ID, Name, Category, Supplier, Quantity, Unit Price, Stock Status badge, and instant action buttons (*"View"* details modal and *"Open ↗"* in inventory).
4. **Flicker-Free Live Refresh**:
   - A dedicated *"Refresh"* button shall re-query SQLite without reconstructing UI widget trees, ensuring zero screen flicker.

---

## FR-16 — Dashboard Quick-Search (Feature 2)

The dashboard shall provide a prominent quick-search field.

The user shall be able to enter a search term and quickly retrieve matching inventory records.

Possible search fields may include:
- Product ID.
- Product Name.
- Category.
- Supplier.

The final searchable fields will be determined during database design.

---

## FR-17 — Search Filters (Feature 3)

The inventory interface shall provide filters allowing the user to narrow the displayed results.

Possible filters include:

- Category.
- Supplier.
- Stock Status.
- Quantity range.
- Price range.

Multiple filters should be capable of being applied together where technically appropriate.

---

## FR-18 — Sorting Options (Feature 4)

The system shall allow inventory records to be sorted according to relevant attributes.

Possible sorting options include:

- Product Name.
- Product ID.
- Quantity.
- Price.
- Category.
- Last Updated.

The user should be able to choose ascending or descending order where applicable.

---

## FR-19 — Database Query Optimization & Indexing (Feature 5)

The application shall use optimized SQLite queries for inventory retrieval.

Where appropriate, database indexes shall be created for frequently searched or filtered columns.

The application shall avoid unnecessarily loading the complete inventory dataset into Python when the database can efficiently perform the required filtering or search operation.

---

## FR-20 — Search Performance Measurement & Benchmarking

The system development process shall include measurement of search/retrieval performance.

Performance measurements may include:

- Query execution time.
- Number of records searched.
- Number of records returned.
- Search performance before optimization.
- Search performance after optimization.

These measurements will provide evidence for evaluating the Q13 quality objective.

---

# 9. Dashboard Requirements

The dashboard shall provide a central interface for accessing important inventory functions.

The dashboard should contain:

- Quick-Search.
- Inventory overview.
- Navigation to inventory management.
- Navigation to Settings.
- Relevant inventory statistics.
- Quick access to commonly used operations.

The dashboard should prioritize rapid access to inventory information.

---

# 10. Settings Requirements

The Settings section shall provide application preferences.

At minimum, it shall provide:

- Keep Me Logged In configuration.
- Account-related settings where applicable.
- Application preferences.

Additional settings may be introduced if they support usability or quality improvement without changing the project's core scope.

## FR-09B - Account Deletion & Database Reset (Danger Zone)

The system shall provide an explicit, password-protected account deletion and database reset capability in the Settings interface.

- The system shall display an explicit, unrecoverable warning modal informing the store/warehouse owner/manager that all stored products, categories, user details, and active sessions will be permanently erased.
- The system shall require the user to re-enter their current master password to confirm deletion.
- If an incorrect or blank password is provided, the system shall reject the action and display an immediate error message.
- Upon valid password confirmation, the system shall execute an atomic wipe of all products, users, and session settings, and run a SQLite VACUUM operation.
- Once reset, the system shall immediately terminate the session and route to the First-Run Setup wizard for clean onboarding.

---

# 11. Database Requirements

## 11.1 Persistent Local Database

The application shall use a persistent SQLite database file.

The database shall not be stored in a temporary location that is automatically deleted when the application closes.

---

## 11.2 Database Transactions

Database modifications shall use appropriate transaction handling.

Successful modifications shall be committed.

Failed operations shall be rolled back where appropriate.

---

## 11.3 Database Integrity

The system shall maintain consistency and integrity of stored inventory data.

Appropriate constraints shall be used where required, such as unique identifiers for inventory records.

---

# 12. Security Requirements

Although the application is offline, authentication shall be implemented to prevent unauthorized access to the application.

The system shall:

- Require authentication before accessing protected functionality.
- Avoid storing passwords as plain-text values where possible.
- Validate login credentials.
- Provide appropriate authentication failure messages.
- Protect local application data from accidental modification through the normal user interface.

Security mechanisms shall remain compatible with the offline architecture.

---

# 13. Non-Functional Requirements

## NFR-01 — Performance

The application should provide fast inventory search and retrieval.

Performance optimization shall be focused particularly on frequently executed search and filtering queries.

---

## NFR-02 — Usability

The interface shall be understandable to a normal computer user without requiring technical knowledge of Python or SQLite.

The main inventory functions should be accessible through clearly labelled GUI controls.

---

## NFR-03 — Reliability

The application should operate consistently without losing valid inventory data during normal use.

Unexpected application errors should be handled gracefully where possible.

---

## NFR-04 — Maintainability

The application shall be developed using a modular structure so that components such as:

- Authentication.
- Database operations.
- Inventory management.
- Search.
- Filtering.
- Sorting.
- Settings.

can be maintained independently.

---

## NFR-05 — Offline Operation

The application shall operate without requiring:

- Internet access.
- Cloud services.
- Online authentication.
- External APIs.

---

## NFR-06 — Portability

The completed application shall be packaged as a Windows executable so that an end user can run the application without manually configuring the Python development environment.

The source code shall remain available in the project's GitHub repository.

---

# 14. Quality Requirements

The primary quality requirement is:

> **The system shall provide fast and efficient retrieval of inventory information while returning accurate and relevant results.**

The project implements five feature areas under the Q13 quality objective:

1. **Dashboard:** Real-time stock statistics, valuation, threshold alerts, and interactive deep links.
2. **Dashboard Quick-Search:** Instant multi-attribute search across Product ID, Name, Category, and Supplier.
3. **Search Filters:** Composable multi-dimensional filtering by Category, Supplier, Stock Status, and text query.
4. **Sorting Options:** Whitelist-validated ascending and descending sorting across all key inventory attributes.
5. **Database Query Optimization:** Strategic SQLite B-tree indexing, WAL concurrency, parameterized queries, and empirical benchmarking.

The effectiveness of these capabilities shall be evaluated using measurable evidence rather than only visual demonstration.

---

# 15. Constraints

The project shall follow the constraints specified by the BBAT104 TQM project guidelines.

### Development constraints

- Python 3.x shall be used.
- VS Code/Visual Studio may be used as the development environment.
- Tkinter/CustomTkinter shall be used for the GUI.
- SQLite3 or file storage shall be used for local persistence.
- GitHub shall be used for source-code version control.
- GitHub Desktop may be used for repository synchronization.

The official guidelines specifically describe this development environment and technology stack.

### Operational constraints

- The application is offline.
- Data is stored locally.
- Internet connectivity is not required.
- Cloud synchronization is not part of the MVP.

---

# 16. Assumptions

The following assumptions are made for Version 1.0:

1. The application is designed for one local user: store or warehouse owner / manager operating on a single local computer.
2. SQLite will be sufficient for the expected inventory dataset.
3. The user has access to a Windows computer for running the packaged application.
4. Inventory data will be managed through the application rather than directly through SQLite.
5. The application will be distributed as a packaged executable after development.
6. The exact inventory fields may be refined during database and UI design.
7. The five Q13-related feature areas constitute the core MVP requirements.

---

# 17. MVP Definition

The minimum viable product shall contain:

### Authentication
- First-run account creation.
- Password login.
- Keep Me Logged In.
- Settings control for Keep Me Logged In.

### Inventory
- Create inventory record.
- Read/view inventory records.
- Update inventory record.
- Delete inventory record.
- Persistent SQLite storage.

### Q13 Quality Features (Five Feature Scope)
- 1. Dashboard (Overview, KPIs, Thresholds, Deep Links).
- 2. Dashboard Quick-Search.
- 3. Search Filters.
- 4. Sorting Options.
- 5. Database Query Optimization & Benchmarking.

### Application
- CustomTkinter GUI.
- Dashboard.
- Settings.
- Error/validation handling.
- Offline operation.

---

# 18. Future Enhancement Possibilities

The following features are outside the current MVP and may be considered only after the core requirements are completed:

- Advanced inventory analytics.
- More detailed dashboards.
- Export functionality.
- Automated backups.
- Multi-user local roles.
- Advanced reporting.
- Additional performance monitoring.

These features must not interfere with completion of the mandatory MVP and TQM requirements.

---

# 19. Acceptance Criteria

The system shall be considered functionally ready for the base-system review when:

1. The application launches successfully.
2. First-time users can create an account.
3. Existing users can authenticate using their password.
4. Keep Me Logged In works as specified.
5. The preference can be changed through Settings.
6. Inventory records can be created.
7. Inventory records can be viewed.
8. Inventory records can be updated.
9. Inventory records can be deleted.
10. Inventory data persists after closing and reopening the application.
11. Dashboard Overview & Real-Time Stock Statistics work with live aggregate calculations and deep links (FR-15).
12. Dashboard Quick-Search rapidly retrieves records across Product ID, Name, Category, and Supplier with reset (FR-16).
13. Search Filters combine Category, Supplier, Stock Status, and text queries with clear action (FR-17).
14. Sorting Options sort all supported columns ascending and descending using strict whitelisting (FR-18).
15. Database Query Optimization, indexes, and parameterized queries are verified via benchmarks (FR-19, FR-20).
16. The application operates completely offline with standalone installer and 100% test pass rate across 55 tests.

---

# 20. Review 1 Deliverables

For Review 1, the project shall provide:

- SRS Document.
- Project Scope Definition.
- System Architecture.
- System Architecture Flowchart.
- GitHub Repository initialization.
- Initial README.md.
- Defined quality objective and requirements.

The official marking scheme identifies **GitHub repository initialization, System Architecture Flowchart, SRS Document, and Scope Definition** as Review 1 deliverables.

---

# 21. Review 2 Preparation

After Review 1, development will proceed toward the base system.

The Review 2 target will be:

- Functional CRUD modules (ProductFormModal, ProductDetailsModal, ConfirmationModal).
- Working authentication (First-run wizard, salted PBKDF2 hashing, Keep Me Logged In, session tokens).
- Working Dashboard (Real-time aggregate KPI statistics, threshold badges, deep links, recent overview).
- Working Dashboard Quick-Search (Instant multi-attribute search across 4 fields with one-click reset).
- Working Search Filters (Category, Supplier, Stock Status, and text query with clear all).
- Working Sorting Options (Whitelist-validated ascending and descending sorting across all 9 supported columns).
- Working SQLite persistence (WAL mode, foreign keys, transaction rollbacks, zero startup database wipe).
- Working Database Query Optimization (Strategic B-tree indexes, parameterized SQL, repeatable multi-dataset benchmark).
- Complete automated verification with 55 passing unit tests and standalone Windows installer (`setup.exe`).

The official guidelines require the base CRUD modules and the assigned quality-goal features for Review 2.

---

# 22. Project Success Definition

The project will be considered successful when it provides a functional offline inventory management system that:

> **Securely stores inventory data locally, provides complete CRUD functionality, and enables users to search, filter, sort, and retrieve inventory information efficiently through an optimized SQLite database.**

The primary measure of project quality will be the system's ability to provide **fast, accurate, and relevant inventory retrieval** while maintaining reliable data persistence and a usable interface.

---

**End of SRS — Version 1.0**