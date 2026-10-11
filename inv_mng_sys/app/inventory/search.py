"""Dashboard Quick-Search and fast product retrieval queries."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Union

from app.database.queries import fetch_all
from app.inventory.crud import Product

logger = logging.getLogger(__name__)


def search_products_quick(
    query: str,
    custom_path: Optional[Union[str, Path]] = None,
) -> List[Product]:
    """Search inventory records across product_id, name, category, and supplier.
    
    Uses indexed SQLite columns for fast retrieval.
    """
    clean_query = query.strip()
    if not clean_query:
        # If query is empty, return latest products
        sql = "SELECT * FROM products ORDER BY updated_at DESC, id DESC LIMIT 100;"
        rows = fetch_all(sql, custom_path=custom_path)
    else:
        term = f"%{clean_query}%"
        sql = """
        SELECT * FROM products
        WHERE product_id LIKE ? OR name LIKE ? OR category LIKE ? OR supplier LIKE ?
        ORDER BY updated_at DESC, id DESC;
        """
        rows = fetch_all(sql, (term, term, term, term), custom_path=custom_path)

    return [Product.from_row(row) for row in rows]
