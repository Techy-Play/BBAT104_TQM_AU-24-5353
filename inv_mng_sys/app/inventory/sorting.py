"""Safe column sorting and ORDER BY clause generation.

Implements strict whitelist-based column and direction validation
to prevent SQL injection and ensure predictable query ordering.
"""

from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Strict whitelist mapping internal identifier / display label to database column
SORT_COLUMN_WHITELIST: Dict[str, str] = {
    "product_id": "product_id",
    "name": "name",
    "category": "category",
    "supplier": "supplier",
    "quantity": "quantity",
    "price": "price",
    "stock_status": "stock_status",
    "updated_at": "updated_at",
    "created_at": "created_at",
    # Human-readable GUI aliases
    "Product ID": "product_id",
    "Product Name": "name",
    "Category": "category",
    "Supplier": "supplier",
    "Quantity": "quantity",
    "Price": "price",
    "Stock Status": "stock_status",
    "Last Updated": "updated_at",
}

# Strict whitelist for sort directions
SORT_DIRECTION_WHITELIST: Dict[str, str] = {
    "asc": "ASC",
    "ascending": "ASC",
    "ASC": "ASC",
    "desc": "DESC",
    "descending": "DESC",
    "DESC": "DESC",
}


def sanitize_sort_column(column_key: str) -> str:
    """Validate and sanitize a requested sort column against the whitelist.
    
    Raises:
        ValueError: If the column is not in the strict whitelist.
    """
    clean_key = str(column_key).strip()
    # Check direct match
    if clean_key in SORT_COLUMN_WHITELIST:
        return SORT_COLUMN_WHITELIST[clean_key]
    
    # Check case-insensitive match
    lower_map = {k.lower(): v for k, v in SORT_COLUMN_WHITELIST.items()}
    if clean_key.lower() in lower_map:
        return lower_map[clean_key.lower()]

    raise ValueError(
        f"Invalid sort column '{column_key}'. Allowed columns: {list(SORT_COLUMN_WHITELIST.keys())}"
    )


def sanitize_sort_direction(direction_key: str) -> str:
    """Validate and sanitize a requested sort direction against the whitelist.
    
    Raises:
        ValueError: If the direction is not 'ASC' or 'DESC'.
    """
    clean_dir = str(direction_key).strip().lower()
    if clean_dir in SORT_DIRECTION_WHITELIST:
        return SORT_DIRECTION_WHITELIST[clean_dir]

    raise ValueError(f"Invalid sort direction '{direction_key}'. Allowed: 'ASC', 'DESC'")


def build_order_by_clause(sort_by: str = "updated_at", direction: str = "desc") -> str:
    """Generate a safe, parameterized ORDER BY SQL fragment.
    
    Guarantees:
    - Never interpolates raw user input.
    - Always uses validated whitelist column names.
    - Uses secondary sort on 'id' for deterministic ordering.
    """
    column = sanitize_sort_column(sort_by)
    direction_sql = sanitize_sort_direction(direction)
    return f"ORDER BY {column} {direction_sql}, id {direction_sql}"
