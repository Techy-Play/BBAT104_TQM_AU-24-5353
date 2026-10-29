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
    low_stock_threshold: int = DEFAULT_LOW_STOCK_THRESHOLD

    @property
    def total_value(self) -> float:
        """Calculate total inventory monetary valuation for this item."""
        return round(self.quantity * self.price, 2)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Product:
        """Construct a Product instance from a SQLite row."""
        threshold = DEFAULT_LOW_STOCK_THRESHOLD
        try:
            if "low_stock_threshold" in row.keys() and row["low_stock_threshold"] is not None:
                threshold = int(row["low_stock_threshold"])
        except Exception:
            threshold = DEFAULT_LOW_STOCK_THRESHOLD

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
            low_stock_threshold=threshold,
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
    low_stock_threshold: Union[int, str] = DEFAULT_LOW_STOCK_THRESHOLD,
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

    # Validate Low Stock Threshold
    try:
        threshold_int = int(low_stock_threshold)
    except (ValueError, TypeError):
        raise ValueError("Low stock threshold must be a valid whole number.")
    if threshold_int < 0:
        raise ValueError("Low stock threshold cannot be negative.")

    # Validate Stock Status
    status_str = determine_stock_status(qty_int, explicit_status=stock_status, threshold=threshold_int)

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
        "low_stock_threshold": threshold_int,
    }


def add_product(
    product_id: str,
    name: str,
    category: str,
    supplier: str,
    quantity: Union[int, str],
    price: Union[float, str],
    stock_status: Optional[str] = None,
    low_stock_threshold: Union[int, str] = DEFAULT_LOW_STOCK_THRESHOLD,
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
        low_stock_threshold=low_stock_threshold,
        custom_path=custom_path,
    )

    sql = """
    INSERT INTO products (product_id, name, category, supplier, quantity, price, stock_status, low_stock_threshold)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
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
            validated["low_stock_threshold"],
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
    low_stock_threshold: Union[int, str] = DEFAULT_LOW_STOCK_THRESHOLD,
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
        low_stock_threshold=low_stock_threshold,
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
        low_stock_threshold = ?,
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
            validated["low_stock_threshold"],
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


def get_shop_owner_analysis(
    custom_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Compute rich inventory and capital analytics for the shop owner dashboard.
    
    Returns:
        Dict containing:
        - summary: total items, total units, total valuation, average SKU value, average unit price
        - health: in-stock, low-stock, out-of-stock counts and percentages
        - categories: breakdown of capital allocation and item counts across categories
        - restock_alerts: prioritized list of products at or below their custom low-stock threshold
    """
    stats = get_inventory_statistics(custom_path=custom_path)
    total_skus = stats["total_products"]
    total_units = stats["total_quantity"]
    total_val = stats["total_value"]
    low_count = stats["low_stock_count"]
    out_count = stats["out_of_stock_count"]
    in_stock_count = max(0, total_skus - low_count - out_count)

    in_stock_pct = round((in_stock_count / total_skus * 100), 1) if total_skus > 0 else 0.0
    low_stock_pct = round((low_count / total_skus * 100), 1) if total_skus > 0 else 0.0
    out_stock_pct = round((out_count / total_skus * 100), 1) if total_skus > 0 else 0.0
    avg_sku_value = round(total_val / total_skus, 2) if total_skus > 0 else 0.0
    avg_unit_price = round(total_val / total_units, 2) if total_units > 0 else 0.0

    # Category Capital Distribution
    cat_sql = """
    SELECT
        category,
        COUNT(*) AS sku_count,
        COALESCE(SUM(quantity), 0) AS units,
        COALESCE(SUM(quantity * price), 0.0) AS category_value
    FROM products
    GROUP BY category
    ORDER BY category_value DESC, sku_count DESC;
    """
    cat_rows = fetch_all(cat_sql, custom_path=custom_path)
    category_breakdown = []
    for r in cat_rows:
        cat_val = round(float(r["category_value"] or 0.0), 2)
        pct_share = round((cat_val / total_val * 100), 1) if total_val > 0 else 0.0
        category_breakdown.append({
            "category": str(r["category"]),
            "sku_count": int(r["sku_count"]),
            "units": int(r["units"]),
            "value": cat_val,
            "percent_share": pct_share,
        })

    # Restock Urgency Alerts (Items at or below custom threshold or out of stock)
    urgency_sql = """
    SELECT id, product_id, name, category, supplier, quantity, price, stock_status, low_stock_threshold
    FROM products
    WHERE quantity <= low_stock_threshold OR stock_status IN ('Low Stock', 'Out of Stock')
    ORDER BY
        CASE WHEN quantity = 0 THEN 0 ELSE 1 END ASC,
        quantity ASC,
        price DESC
    LIMIT 20;
    """
    urgency_rows = fetch_all(urgency_sql, custom_path=custom_path)
    restock_items = []
    for r in urgency_rows:
        qty = int(r["quantity"])
        thresh = int(r["low_stock_threshold"]) if "low_stock_threshold" in r.keys() and r["low_stock_threshold"] is not None else 10
        shortage = max(0, thresh - qty)
        restock_items.append({
            "id": r["id"],
            "product_id": r["product_id"],
            "name": r["name"],
            "category": r["category"],
            "supplier": r["supplier"],
            "quantity": qty,
            "threshold": thresh,
            "shortage": shortage,
            "price": float(r["price"]),
            "stock_status": r["stock_status"],
            "urgency": "CRITICAL" if qty == 0 else ("HIGH" if qty <= (thresh // 2) else "WARNING"),
        })

    return {
        "total_skus": total_skus,
        "total_units": total_units,
        "total_value": total_val,
        "avg_sku_value": avg_sku_value,
        "avg_unit_price": avg_unit_price,
        "in_stock_count": in_stock_count,
        "low_stock_count": low_count,
        "out_of_stock_count": out_count,
        "in_stock_pct": in_stock_pct,
        "low_stock_pct": low_stock_pct,
        "out_stock_pct": out_stock_pct,
        "categories": category_breakdown,
        "restock_alerts": restock_items,
    }
