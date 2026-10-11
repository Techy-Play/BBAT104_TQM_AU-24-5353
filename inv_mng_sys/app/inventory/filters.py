"""Inventory multi-attribute search and filtering engine.

Implements combined filtering across:
- Text search (Product ID, Name, Category, Supplier)
- Exact Category filter
- Exact Supplier filter
- Exact Stock Status filter
- Optional numeric ranges (Price and Quantity)
- Integrated whitelist sorting
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from app.database.queries import fetch_all
from app.inventory.crud import Product
from app.inventory.sorting import build_order_by_clause

logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    """Encapsulates all search and filter parameters for inventory querying."""

    search_query: Optional[str] = None
    category: Optional[str] = None
    supplier: Optional[str] = None
    stock_status: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_quantity: Optional[int] = None
    max_quantity: Optional[int] = None
    sort_by: str = "updated_at"
    sort_direction: str = "desc"

    def is_filtered(self) -> bool:
        """Return True if any non-default filter condition is active."""
        if self.search_query and self.search_query.strip():
            return True
        if self.category and self.category.strip() and self.category.strip().lower() != "all":
            return True
        if self.supplier and self.supplier.strip() and self.supplier.strip().lower() != "all":
            return True
        if self.stock_status and self.stock_status.strip() and self.stock_status.strip().lower() != "all":
            return True
        if self.min_price is not None or self.max_price is not None:
            return True
        if self.min_quantity is not None or self.max_quantity is not None:
            return True
        return False


def get_distinct_categories(custom_path: Optional[Union[str, Path]] = None) -> List[str]:
    """Retrieve sorted list of distinct categories currently in the database."""
    sql = "SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND TRIM(category) != '' ORDER BY category COLLATE NOCASE ASC;"
    rows = fetch_all(sql, custom_path=custom_path)
    return [row["category"] for row in rows]


def get_distinct_suppliers(custom_path: Optional[Union[str, Path]] = None) -> List[str]:
    """Retrieve sorted list of distinct suppliers currently in the database."""
    sql = "SELECT DISTINCT supplier FROM products WHERE supplier IS NOT NULL AND TRIM(supplier) != '' ORDER BY supplier COLLATE NOCASE ASC;"
    rows = fetch_all(sql, custom_path=custom_path)
    return [row["supplier"] for row in rows]


def filter_products(
    criteria: Optional[FilterCriteria] = None,
    custom_path: Optional[Union[str, Path]] = None,
) -> List[Product]:
    """Execute parameterized query applying combined filters and safe sorting.
    
    Guarantees:
    - 100% parameterized SQL.
    - Whitelist-validated ORDER BY clause.
    - Handles any combination of active filters.
    """
    if criteria is None:
        criteria = FilterCriteria()

    clauses: List[str] = []
    params: List[Any] = []

    # 1. Text Search across product_id, name, category, supplier
    if criteria.search_query and criteria.search_query.strip():
        term = f"%{criteria.search_query.strip()}%"
        clauses.append("(product_id LIKE ? OR name LIKE ? OR category LIKE ? OR supplier LIKE ?)")
        params.extend([term, term, term, term])

    # 2. Category Filter (Case-insensitive match)
    if criteria.category and criteria.category.strip() and criteria.category.strip().lower() != "all":
        clauses.append("category = ? COLLATE NOCASE")
        params.append(criteria.category.strip())

    # 3. Supplier Filter (Case-insensitive match)
    if criteria.supplier and criteria.supplier.strip() and criteria.supplier.strip().lower() != "all":
        clauses.append("supplier = ? COLLATE NOCASE")
        params.append(criteria.supplier.strip())

    # 4. Stock Status Filter
    if criteria.stock_status and criteria.stock_status.strip() and criteria.stock_status.strip().lower() != "all":
        clauses.append("stock_status = ?")
        params.append(criteria.stock_status.strip())

    # 5. Price Range
    if criteria.min_price is not None:
        clauses.append("price >= ?")
        params.append(float(criteria.min_price))
    if criteria.max_price is not None:
        clauses.append("price <= ?")
        params.append(float(criteria.max_price))

    # 6. Quantity Range
    if criteria.min_quantity is not None:
        clauses.append("quantity >= ?")
        params.append(int(criteria.min_quantity))
    if criteria.max_quantity is not None:
        clauses.append("quantity <= ?")
        params.append(int(criteria.max_quantity))

    # Assemble SQL
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order_by_sql = build_order_by_clause(criteria.sort_by, criteria.sort_direction)

    sql = f"SELECT * FROM products {where_sql} {order_by_sql};"

    rows = fetch_all(sql, params, custom_path=custom_path)
    return [Product.from_row(r) for r in rows]
