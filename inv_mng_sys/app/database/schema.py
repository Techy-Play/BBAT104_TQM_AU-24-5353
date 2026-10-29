"""Database schema definition, indexes, and initialization logic.

Aligns with BBAT104 project specifications and SRS requirements:
- Q13: Faster Search & Retrieval (indexes on product_id, name, category, supplier, stock_status)
- Local authentication and user profile storage
- Persistent offline inventory storage
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import sqlite3

from app.database.connection import create_connection, get_database_path

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = "1.1.0"

# DDL for persistent tables
CREATE_TABLES_SQL = """
-- Users table: Local authentication credentials and profile information
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    organization_name TEXT NOT NULL,
    keep_logged_in INTEGER NOT NULL DEFAULT 0 CHECK (keep_logged_in IN (0, 1)),
    session_token TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Products table: Inventory items matching SRS.md Section 7 & Section 11
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    supplier TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    price REAL NOT NULL DEFAULT 0.0 CHECK (price >= 0.0),
    stock_status TEXT NOT NULL DEFAULT 'In Stock' CHECK (stock_status IN ('In Stock', 'Low Stock', 'Out of Stock')),
    low_stock_threshold INTEGER NOT NULL DEFAULT 10 CHECK (low_stock_threshold >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Application settings and persistent local configuration
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# DDL for performance indexes justified by Q13 (Faster Search & Retrieval)
CREATE_INDEXES_SQL = """
-- Unique index on product_id for fast SKU lookup and uniqueness enforcement
CREATE UNIQUE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);

-- Case-insensitive index on product name for Dashboard Quick-Search
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name COLLATE NOCASE);

-- Index on category for inventory category filtering
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category COLLATE NOCASE);

-- Index on supplier for inventory supplier filtering and search
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier COLLATE NOCASE);

-- Index on stock_status for inventory stock-level filtering
CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(stock_status);

-- Composite index on (category, supplier) for combined multi-attribute filters
CREATE INDEX IF NOT EXISTS idx_products_cat_sup ON products(category COLLATE NOCASE, supplier COLLATE NOCASE);

-- Index on username for fast login lookup
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username COLLATE NOCASE);
"""

# Triggers for maintaining updated_at timestamps automatically
CREATE_TRIGGERS_SQL = """
CREATE TRIGGER IF NOT EXISTS trg_products_updated_at
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
"""


def init_database(custom_path: Optional[Union[str, Path]] = None) -> Dict[str, Union[bool, str, List[str]]]:
    """Initialize database tables, indexes, and initial metadata.
    
    Guarantees:
    - Never drops existing tables or deletes existing user records.
    - Idempotent: safe to run on every application startup.
    - Sets schema_version in app_settings if not already present.
    
    Returns:
        Dict detailing initialization status and present tables.
    """
    db_path = get_database_path(custom_path)
    existed_before = db_path.is_file() and db_path.stat().st_size > 0

    conn = create_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            # Execute table, index, and trigger creation scripts
            cursor.executescript(CREATE_TABLES_SQL)
            cursor.executescript(CREATE_INDEXES_SQL)
            cursor.executescript(CREATE_TRIGGERS_SQL)

            # Column migration: Ensure low_stock_threshold exists in existing products table
            cursor.execute("PRAGMA table_info(products);")
            columns = [col["name"] for col in cursor.fetchall()]
            if "low_stock_threshold" not in columns:
                try:
                    cursor.execute("ALTER TABLE products ADD COLUMN low_stock_threshold INTEGER NOT NULL DEFAULT 10 CHECK (low_stock_threshold >= 0);")
                    logger.info("Migrated products table: added low_stock_threshold column.")
                except sqlite3.OperationalError as e:
                    logger.debug("Column migration note: %s", e)

            # Record schema version metadata if absent
            cursor.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES ('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                """,
                (CURRENT_SCHEMA_VERSION,),
            )

        # Retrieve table names to verify initialization
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        tables = [row["name"] for row in cursor.fetchall()]

        # Retrieve index names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        indexes = [row["name"] for row in cursor.fetchall()]

        logger.info(
            "Database initialized at %s (existed_before=%s, tables=%s, indexes=%s)",
            db_path,
            existed_before,
            tables,
            indexes,
        )

        return {
            "success": True,
            "database_path": str(db_path),
            "existed_before": existed_before,
            "tables": tables,
            "indexes": indexes,
            "schema_version": CURRENT_SCHEMA_VERSION,
        }
    finally:
        conn.close()
