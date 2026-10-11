"""Inventory CRUD domain operations and validation logic.

Fulfills Phase 6 requirements:
- Create (Add product)
- Read (Retrieve product by ID/SKU, list all products)
- Update (Edit product attributes)
- Delete (Remove product)
- Inventory statistics aggregation for Dashboard (Phase 5)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import sqlite3

from app.database.connection import get_db_connection
from app.database.queries import (
    execute_insert,
    execute_update_or_delete,
    fetch_all,
    fetch_one,
)

logger = logging.getLogger(__name__)

PRODUCT_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{2,50}$")
VALID_STOCK_STATUSES = ("In Stock", "Low Stock", "Out of Stock")
DEFAULT_LOW_STOCK_THRESHOLD = 10


@dataclass(frozen=True)
class Product:
    """Immutable representation of an inventory product record."""

    id: int
    product_id: str
    name: str
    category: str
    supplier: str
    quantity: int
    price: float
    stock_status: str
    created_at: str
    updated_at: str

    @property
    def total_value(self) -> float:
        """Calculate total inventory monetary valuation for this item."""
        return round(self.quantity * self.price, 2)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Product:
        """Construct a Product instance from a SQLite row."""
        return cls(
            id=row["id"],
            product_id=row["product_id"],
            name=row["name"],
            category=row["category"],
            supplier=row["supplier"],
            quantity=int(row["quantity"]),
            price=float(row["price"]),
            stock_status=row["stock_status"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


def determine_stock_status(
    quantity: int,
    explicit_status: Optional[str] = None,
    threshold: int = DEFAULT_LOW_STOCK_THRESHOLD,
) -> str:
    """Determine the appropriate stock status based on quantity and threshold rules."""
    if quantity <= 0:
        return "Out of Stock"
    if explicit_status in VALID_STOCK_STATUSES:
        if explicit_status == "Out of Stock" and quantity > 0:
            return "Low Stock" if quantity <= threshold else "In Stock"
        return explicit_status
    if quantity <= threshold:
        return "Low Stock"
    return "In Stock"


def validate_product_data(
    product_id: str,
    name: str,
    category: str,
    supplier: str,
    quantity: Union[int, str],
    price: Union[float, str],
    stock_status: Optional[str] = None,
    exclude_id: Optional[int] = None,
    custom_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Validate product fields against business rules and SQLite constraints.
    
    Returns:
        Dict containing sanitized fields.
        
    Raises:
        ValueError: If any validation rule is violated.
    """
    clean_sku = str(product_id).strip()
    clean_name = str(name).strip()
    clean_cat = str(category).strip()
    clean_sup = str(supplier).strip()

    if not clean_sku:
        raise ValueError("Product ID / SKU is required.")
    if not PRODUCT_ID_REGEX.match(clean_sku):
        raise ValueError("Product ID must be 2-50 characters (letters, numbers, hyphens, periods, or underscores).")

    if not clean_name:
        raise ValueError("Product Name is required.")
    if len(clean_name) < 2:
        raise ValueError("Product Name must be at least 2 characters long.")

    if not clean_cat:
        raise ValueError("Category is required.")
    if len(clean_cat) < 2:
        raise ValueError("Category must be at least 2 characters long.")

    if not clean_sup:
        raise ValueError("Supplier is required.")
    if len(clean_sup) < 2:
        raise ValueError("Supplier must be at least 2 characters long.")

    # Validate Quantity
    try:
        qty_int = int(quantity)
    except (ValueError, TypeError):
        raise ValueError("Quantity must be a valid whole number.")
    if qty_int < 0:
        raise ValueError("Quantity cannot be negative.")

    # Validate Price
    try:
        price_flt = round(float(price), 2)
    except (ValueError, TypeError):
        raise ValueError("Price must be a valid numeric amount.")
    if price_flt < 0.0:
        raise ValueError("Price cannot be negative.")

    # Validate Stock Status
    status_str = determine_stock_status(qty_int, explicit_status=stock_status)

    # Check Product ID Uniqueness
    if exclude_id is not None:
        check_sql = "SELECT id FROM products WHERE product_id = ? COLLATE NOCASE AND id != ?;"
        existing = fetch_one(check_sql, (clean_sku, exclude_id), custom_path=custom_path)
    else:
        check_sql = "SELECT id FROM products WHERE product_id = ? COLLATE NOCASE;"
        existing = fetch_one(check_sql, (clean_sku,), custom_path=custom_path)

    if existing:
        raise ValueError(f"Product ID '{clean_sku}' already exists. Product IDs must be unique.")

    return {
        "product_id": clean_sku,
        "name": clean_name,
        "category": clean_cat,
        "supplier": clean_sup,
        "quantity": qty_int,
        "price": price_flt,
        "stock_status": status_str,
    }


def add_product(
    product_id: str,
    name: str,
    category: str,
    supplier: str,
    quantity: Union[int, str],
    price: Union[float, str],
    stock_status: Optional[str] = None,
    custom_path: Optional[Union[str, Path]] = None,
) -> Product:
    """Create and persist a new inventory product record."""
    validated = validate_product_data(
        product_id=product_id,
        name=name,
        category=category,
        supplier=supplier,
        quantity=quantity,
        price=price,
        stock_status=stock_status,
        custom_path=custom_path,
    )

    sql = """
    INSERT INTO products (product_id, name, category, supplier, quantity, price, stock_status)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    row_id = execute_insert(
        sql,
        (
            validated["product_id"],
            validated["name"],
            validated["category"],
            validated["supplier"],
            validated["quantity"],
            validated["price"],
            validated["stock_status"],
        ),
        custom_path=custom_path,
    )

    product = get_product_by_id(row_id, custom_path=custom_path)
    if not product:
        raise RuntimeError("Failed to retrieve product after insertion.")

    logger.info("Created product '%s' (%s) with ID %d.", product.name, product.product_id, row_id)
    return product


def get_product_by_id(
    item_id: int,
    custom_path: Optional[Union[str, Path]] = None,
) -> Optional[Product]:
    """Retrieve a single product by primary key ID."""
    row = fetch_one("SELECT * FROM products WHERE id = ?;", (item_id,), custom_path=custom_path)
    return Product.from_row(row) if row else None


def get_product_by_product_id(
    product_id: str,
    custom_path: Optional[Union[str, Path]] = None,
) -> Optional[Product]:
    """Retrieve a product by user SKU / Product ID."""
    clean_sku = str(product_id).strip()
    row = fetch_one(
        "SELECT * FROM products WHERE product_id = ? COLLATE NOCASE;",
        (clean_sku,),
        custom_path=custom_path,
    )
    return Product.from_row(row) if row else None


def get_all_products(
    search_query: Optional[str] = None,
    custom_path: Optional[Union[str, Path]] = None,
) -> List[Product]:
    """Retrieve all products, optionally filtered by a search query."""
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        sql = """
        SELECT * FROM products
        WHERE product_id LIKE ? OR name LIKE ? OR category LIKE ? OR supplier LIKE ?
        ORDER BY updated_at DESC, id DESC;
        """
        rows = fetch_all(sql, (term, term, term, term), custom_path=custom_path)
    else:
        sql = "SELECT * FROM products ORDER BY updated_at DESC, id DESC;"
        rows = fetch_all(sql, custom_path=custom_path)

    return [Product.from_row(r) for r in rows]


def update_product(
    item_id: int,
    product_id: str,
    name: str,
    category: str,
    supplier: str,
    quantity: Union[int, str],
    price: Union[float, str],
    stock_status: Optional[str] = None,
    custom_path: Optional[Union[str, Path]] = None,
) -> Product:
    """Update an existing product record."""
    existing = get_product_by_id(item_id, custom_path=custom_path)
    if not existing:
        raise ValueError(f"Product with ID {item_id} does not exist.")

    validated = validate_product_data(
        product_id=product_id,
        name=name,
        category=category,
        supplier=supplier,
        quantity=quantity,
        price=price,
        stock_status=stock_status,
        exclude_id=item_id,
        custom_path=custom_path,
    )

    sql = """
    UPDATE products
    SET product_id = ?,
        name = ?,
        category = ?,
        supplier = ?,
        quantity = ?,
        price = ?,
        stock_status = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?;
    """
    rows_affected = execute_update_or_delete(
        sql,
        (
            validated["product_id"],
            validated["name"],
            validated["category"],
            validated["supplier"],
            validated["quantity"],
            validated["price"],
            validated["stock_status"],
            item_id,
        ),
        custom_path=custom_path,
    )

    if rows_affected == 0:
        raise RuntimeError(f"Update failed for product ID {item_id}.")

    updated = get_product_by_id(item_id, custom_path=custom_path)
    if not updated:
        raise RuntimeError("Failed to retrieve product after update.")

    logger.info("Updated product ID %d ('%s').", item_id, updated.name)
    return updated


def delete_product(
    item_id: int,
    custom_path: Optional[Union[str, Path]] = None,
) -> bool:
    """Delete a product by primary key ID."""
    existing = get_product_by_id(item_id, custom_path=custom_path)
    if not existing:
        raise ValueError(f"Product with ID {item_id} does not exist.")

    rows = execute_update_or_delete(
        "DELETE FROM products WHERE id = ?;",
        (item_id,),
        custom_path=custom_path,
    )
    success = rows > 0
    if success:
        logger.info("Deleted product ID %d ('%s').", item_id, existing.name)
    return success


def get_inventory_statistics(
    custom_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Compute aggregate inventory statistics from actual SQLite records."""
    sql = """
    SELECT
        COUNT(*) AS total_products,
        COALESCE(SUM(quantity), 0) AS total_quantity,
        COALESCE(SUM(quantity * price), 0.0) AS total_value,
        SUM(CASE WHEN stock_status = 'Low Stock' THEN 1 ELSE 0 END) AS low_stock_count,
        SUM(CASE WHEN stock_status = 'Out of Stock' THEN 1 ELSE 0 END) AS out_of_stock_count,
        COUNT(DISTINCT category) AS total_categories
    FROM products;
    """
    row = fetch_one(sql, custom_path=custom_path)
    if not row:
        return {
            "total_products": 0,
            "total_quantity": 0,
            "total_value": 0.0,
            "low_stock_count": 0,
            "out_of_stock_count": 0,
            "total_categories": 0,
        }

    return {
        "total_products": int(row["total_products"] or 0),
        "total_quantity": int(row["total_quantity"] or 0),
        "total_value": round(float(row["total_value"] or 0.0), 2),
        "low_stock_count": int(row["low_stock_count"] or 0),
        "out_of_stock_count": int(row["out_of_stock_count"] or 0),
        "total_categories": int(row["total_categories"] or 0),
    }
