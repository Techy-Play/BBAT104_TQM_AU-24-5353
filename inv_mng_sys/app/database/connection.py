"""SQLite Database Connection Layer.

Provides persistent database path resolution, connection factories,
PRAGMA configuration for offline desktop performance and data integrity,
and transaction context management.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
from typing import Generator, Optional, Union

logger = logging.getLogger(__name__)

# Base path of the inv_mng_sys project
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_default_db_path() -> Path:
    """Determine default database path based on runtime environment."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        portable_db_dir = exe_dir / "database"
        # If user explicitly placed a writable database folder next to exe, use it
        if portable_db_dir.exists() and os.access(portable_db_dir, os.W_OK):
            return portable_db_dir / "ims.db"
        # Standard Windows persistent user storage for installed applications
        appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "InventoryManagementSystem" / "database" / "ims.db"
        return portable_db_dir / "ims.db"
    return PROJECT_ROOT / "database" / "ims.db"


# Default production database path
DEFAULT_DB_PATH = _resolve_default_db_path()


def get_database_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve and return the absolute database file path.
    
    Order of precedence:
    1. Explicit custom_path argument (e.g., for testing)
    2. IMS_DATABASE_PATH environment variable
    3. Default persistent path: LOCALAPPDATA (if frozen) or inv_mng_sys/database/ims.db
    """
    if custom_path is not None:
        target_path = Path(custom_path)
    elif "IMS_DATABASE_PATH" in os.environ:
        target_path = Path(os.environ["IMS_DATABASE_PATH"])
    else:
        target_path = _resolve_default_db_path()

    # Ensure parent directory exists for persistent local storage
    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path.resolve()


def database_exists(custom_path: Optional[Union[str, Path]] = None) -> bool:
    """Check if the target database file already exists on disk."""
    path = get_database_path(custom_path)
    return path.is_file() and path.stat().st_size > 0


def create_connection(
    custom_path: Optional[Union[str, Path]] = None,
    timeout: float = 5.0,
) -> sqlite3.Connection:
    """Create and configure a new SQLite connection.
    
    Enforces:
    - Foreign key constraints (PRAGMA foreign_keys = ON)
    - Write-Ahead Logging for concurrency and recovery (PRAGMA journal_mode = WAL)
    - Synchronous mode NORMAL for optimal balance of safety and speed
    - Row factory configured to sqlite3.Row for dict-like and index-based column access
    """
    db_path = get_database_path(custom_path)
    
    conn = sqlite3.connect(
        database=str(db_path),
        timeout=timeout,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    
    # Configure row access by column name
    conn.row_factory = sqlite3.Row

    # Enforce SQLite PRAGMAs for performance, safety, and integrity
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.close()

    return conn


@contextmanager
def get_db_connection(
    custom_path: Optional[Union[str, Path]] = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections handling transactions.
    
    Automatically commits on successful exit or rolls back if an exception is raised.
    Always closes the connection upon completion.
    """
    conn = create_connection(custom_path)
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Transaction rolled back due to error: %s", exc)
        raise
    finally:
        conn.close()
