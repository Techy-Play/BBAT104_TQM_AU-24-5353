# Database Architecture & Design Specification

## Overview

The **Inventory Management System (IMS)** utilizes **SQLite 3** as its persistent local database engine.
As specified in the course SRS (BBAT104) and project guidelines:
- **Offline First**: The database is fully local; no network connection or remote database is required.
- **Persistent Storage**: Production database data persists in `inv_mng_sys/database/ims.db`. It is never cleared or reset on application startup.
- **Q13 Core Goal**: Optimized schema, explicit indexes, and parameterized queries ensure high-speed search and retrieval for inventory records.

---

## 1. Connection Architecture & SQLite PRAGMAs

SQLite connections are managed through `app/database/connection.py`. Every connection applies the following engine PRAGMAs upon opening:

1. `PRAGMA foreign_keys = ON;`  
   Enforces referential integrity across related tables.
2. `PRAGMA journal_mode = WAL;`  
   Write-Ahead Logging enables concurrent reads and writes, improves write throughput, and minimizes transaction lock contention.
3. `PRAGMA synchronous = NORMAL;`  
   In WAL mode, provides strong durability against application crashes while eliminating disk I/O bottlenecks.
4. `PRAGMA busy_timeout = 5000;`  
   Sets a 5-second wait timeout if another thread or process is locking the file, preventing `database is locked` crashes.

### Transaction Management
The `get_db_connection()` context manager ensures atomic operations:
- Automatically issues `COMMIT` upon clean code block execution.
- Automatically issues `ROLLBACK` and logs the exception if an error occurs.
- Guarantees `CLOSE` in a `finally` block to prevent resource leaks.

---

## 2. Table Schemas

### 2.1 `users` Table
Stores local user profile details, credentials, and authentication preferences.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique internal user ID |
| `username` | TEXT | NOT NULL, UNIQUE, COLLATE NOCASE | Case-insensitive local login username |
| `password_hash` | TEXT | NOT NULL | Salted PBKDF2/SHA-256 hash |
| `salt` | TEXT | NOT NULL | Cryptographic salt (hex-encoded) |
| `full_name` | TEXT | NOT NULL | Full name of user (e.g. "Lokesh Paneru") |
| `organization_name` | TEXT | NOT NULL | Store / Warehouse / Business name |
| `keep_logged_in` | INTEGER | NOT NULL DEFAULT 0, CHECK (0, 1) | Remember login session flag |
| `session_token` | TEXT | NULLABLE | Local session authentication token |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last profile modification timestamp |

### 2.2 `products` Table
Stores all inventory items. Corresponds directly to SRS Section 7 (FR-10 to FR-14).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `product_id` | TEXT | NOT NULL, UNIQUE, COLLATE NOCASE | Unique user SKU / barcode identifier |
| `name` | TEXT | NOT NULL | Item name |
| `category` | TEXT | NOT NULL | Product category (e.g., Electronics, Hardware) |
| `supplier` | TEXT | NOT NULL | Supplier / vendor name |
| `quantity` | INTEGER | NOT NULL DEFAULT 0, CHECK (quantity >= 0) | Current stock quantity |
| `price` | REAL | NOT NULL DEFAULT 0.0, CHECK (price >= 0.0) | Unit price |
| `stock_status` | TEXT | NOT NULL DEFAULT 'In Stock' | 'In Stock', 'Low Stock', 'Out of Stock' |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when record was created |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when record was last updated |

### 2.3 `app_settings` Table
Key-value store for application configuration, active local sessions, and schema versions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `key` | TEXT | PRIMARY KEY | Configuration key name (e.g., `schema_version`) |
| `value` | TEXT | NOT NULL | Configuration value |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last modified timestamp |

---

## 3. Q13 Performance Indexes & Justification

To fulfill **Q13 — Faster Search & Retrieval**, SQLite B-Tree indexes are created for attributes that are frequently queried, filtered, or sorted:

| Index Name | Target Column(s) | Justification & Use Case |
|---|---|---|
| `idx_products_product_id` | `product_id` | Instant O(log N) lookup by SKU/Product ID in Quick-Search. |
| `idx_products_name` | `name COLLATE NOCASE` | Fast case-insensitive prefix and substring searches in Quick-Search. |
| `idx_products_category` | `category COLLATE NOCASE` | Speeds up category filter dropdown queries and category grouping. |
| `idx_products_supplier` | `supplier COLLATE NOCASE` | Speeds up supplier filter dropdown queries and supplier searches. |
| `idx_products_stock_status` | `stock_status` | Instant filtering for low-stock warnings and inventory status tabs. |
| `idx_products_cat_sup` | `(category, supplier)` | Composite index optimizing multi-criteria queries when filtering by both category and supplier simultaneously. |
| `idx_users_username` | `username COLLATE NOCASE` | Instant O(log N) user lookup during login. |

---

## 4. Automatic Update Triggers

To maintain audit integrity without manual application code overhead, SQLite `AFTER UPDATE` triggers update `updated_at`:
- `trg_products_updated_at`: Automatically sets `updated_at = CURRENT_TIMESTAMP` when any product column is modified.
- `trg_users_updated_at`: Automatically sets `updated_at = CURRENT_TIMESTAMP` when user details change.

---

## 5. Phase 3 & Phase 4: Authentication & Session Data Storage

### 5.1 Credential & Salt Storage
- **Password Hashes**: Computed using PBKDF2-HMAC-SHA256 (100,000 iterations). Stored as a 64-character hexadecimal string in `users.password_hash`.
- **Salts**: 32-character hexadecimal random salts generated per user via `secrets.token_hex(16)` and stored in `users.salt`.
- **Plaintext Passwords**: Strictly prohibited. No unhashed password is ever written to SQLite or stored in logs.

### 5.2 Session Token Lifecycle & App Settings
- **`active_session_token`**: Stored in `app_settings` under key `'active_session_token'`. Points to the currently active session token on this local machine.
- **Login with Keep Me Logged In**: A 64-character random token is generated and saved in both `users.session_token` and `app_settings.active_session_token`. `users.keep_logged_in` is set to `1`.
- **Login without Keep Me Logged In**: `users.session_token` is cleared (`NULL`), `users.keep_logged_in` is set to `0`, and `app_settings.active_session_token` is cleared (`''`).
- **Logout**: Clears `users.session_token` (`NULL`), resets `keep_logged_in` (`0`), and empties `active_session_token` in `app_settings`.

