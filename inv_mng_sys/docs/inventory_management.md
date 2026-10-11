# Inventory Management & CRUD Specification

## Overview

The **Inventory Management System (IMS)** provides persistent local inventory tracking adhering to the BBAT104 TQM course requirements. Phase 5 and Phase 6 establish:
1. **Interactive Dashboard**: Real-time aggregate statistics, personalized greetings, quick-search, and recent item overview.
2. **Complete Inventory CRUD**: Adding, viewing, updating, and deleting products with strict validation and user confirmation.

---

## 1. Domain Model & Product Schema

Inventory records are stored in the persistent SQLite `products` table and represented by the immutable `Product` dataclass (`app/inventory/crud.py`).

| Field | Type | SQLite Constraint | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key identifier |
| `product_id` | TEXT | UNIQUE, NOT NULL, COLLATE NOCASE | User-facing SKU or barcode (2–50 alphanumeric chars) |
| `name` | TEXT | NOT NULL | Product name (minimum 2 characters) |
| `category` | TEXT | NOT NULL | Product grouping (indexed for retrieval) |
| `supplier` | TEXT | NOT NULL | Vendor or distributor name (indexed) |
| `quantity` | INTEGER | NOT NULL, CHECK(quantity >= 0) | Physical stock count |
| `price` | REAL | NOT NULL, CHECK(price >= 0.0) | Unit price in local currency ($) |
| `stock_status` | TEXT | CHECK(stock_status IN ('In Stock', 'Low Stock', 'Out of Stock')) | Current inventory state |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Automatic trigger-updated timestamp |

### Computed Properties
- `Product.total_value`: `quantity * price`, providing real-time item valuation.

---

## 2. Validation & Stock Status Rules

All inputs are sanitized and verified before reaching SQLite transactions:
1. **Product ID Uniqueness**: Verified case-insensitively. Duplicate SKU creation is rejected with a user-friendly error. On editing, unique SKU conflicts are checked excluding the item being modified.
2. **Numeric Integrity**: Quantities must be non-negative integers; prices must be non-negative numbers rounded to two decimal places.
3. **Empty Field Rejection**: Product ID, Name, Category, and Supplier cannot be blank or whitespace-only.
4. **Stock Status Behavior**:
   - `quantity == 0`: Automatically marked as **Out of Stock**.
   - `1 <= quantity <= 10`: Automatically flagged as **Low Stock**.
   - `quantity > 10`: Marked as **In Stock**.
   - Manual override is permitted if compatible with the physical quantity.

---

## 3. CRUD Workflow

```text
User Action (GUI)
       │
       ▼
Modal Dialog (ProductFormModal) ──► Input Validation (validate_product_data)
       │                                     │
       ▼                                     ▼
SQLite Transaction (Parameterized SQL)  Raise Friendly Error
       │
       ├─── INSERT (add_product)
       ├─── SELECT (get_product_by_id / get_all_products)
       ├─── UPDATE (update_product)
       └─── DELETE (delete_product after ConfirmationModal)
       │
       ▼
Emit Data Changed Signal ──► Refresh Dashboard Stats & Table View
```

### Safety & Confirmation
- **Destructive Deletion**: Deletion cannot occur accidentally. A `ConfirmationModal` requires explicit confirmation before issuing a `DELETE` transaction.
- **Transactions**: Atomic execution ensures partial modifications roll back if any constraint fails.

---

## 4. Dashboard Aggregate Statistics

The dashboard computes real-time metrics using SQLite aggregate functions via `get_inventory_statistics()`:

```sql
SELECT
    COUNT(*) AS total_products,
    COALESCE(SUM(quantity), 0) AS total_quantity,
    COALESCE(SUM(quantity * price), 0.0) AS total_value,
    SUM(CASE WHEN stock_status = 'Low Stock' THEN 1 ELSE 0 END) AS low_stock_count,
    SUM(CASE WHEN stock_status = 'Out of Stock' THEN 1 ELSE 0 END) AS out_of_stock_count,
    COUNT(DISTINCT category) AS total_categories
FROM products;
```

---

## 5. Automated Verification

The test suite in [`tests/test_inventory_crud.py`](../tests/test_inventory_crud.py) covers:
- Product creation, retrieval, updates, and deletion.
- Duplicate SKU rejection on insert and update.
- Non-negative validation on quantity and price.
- Empty required field rejections.
- Stock status calculation logic.
- Persistence across simulated application restarts.
- Accurate dashboard aggregate metrics using actual database records.
- Dashboard quick-search retrieval.
