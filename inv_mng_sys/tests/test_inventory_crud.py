"""Automated tests for Phase 5 (Dashboard Statistics) and Phase 6 (Inventory CRUD).

Validates:
1. Product creation with validation and stock status computation.
2. Product listing and retrieval by ID / SKU.
3. Product updates and timestamp modification.
4. Product deletion.
5. Unique Product ID enforcement (creation and update).
6. Non-negative quantity and price constraints.
7. Empty required field rejections.
8. Data persistence across database closure and reopen.
9. Dashboard aggregate statistics calculated from actual records.
10. Dashboard quick-search retrieval.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from app.database.schema import init_database
from app.inventory.crud import (
    add_product,
    delete_product,
    determine_stock_status,
    get_all_products,
    get_inventory_statistics,
    get_product_by_id,
    get_product_by_product_id,
    update_product,
    validate_product_data,
)
from app.inventory.search import search_products_quick


class TestInventoryCRUDAndDashboard(unittest.TestCase):
    """Test suite for Phase 5 and Phase 6 inventory operations and metrics."""

    def setUp(self) -> None:
        """Create an isolated temporary SQLite database for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_inventory.db"
        init_database(self.db_path)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_product_creation(self) -> None:
        """Confirm valid product creation and attribute persistence."""
        prod = add_product(
            product_id="SKU-1001",
            name="Digital Multimeter",
            category="Electronics",
            supplier="VoltTech Ltd.",
            quantity=25,
            price=49.99,
            custom_path=self.db_path,
        )

        self.assertIsNotNone(prod)
        self.assertEqual(prod.product_id, "SKU-1001")
        self.assertEqual(prod.name, "Digital Multimeter")
        self.assertEqual(prod.category, "Electronics")
        self.assertEqual(prod.supplier, "VoltTech Ltd.")
        self.assertEqual(prod.quantity, 25)
        self.assertEqual(prod.price, 49.99)
        self.assertEqual(prod.stock_status, "In Stock")
        self.assertEqual(prod.total_value, round(25 * 49.99, 2))

    def test_02_product_retrieval(self) -> None:
        """Confirm product retrieval by primary ID and unique SKU."""
        created = add_product(
            product_id="SKU-2002",
            name="Soldering Station",
            category="Tools",
            supplier="Weller Co.",
            quantity=8,
            price=89.50,
            custom_path=self.db_path,
        )

        by_id = get_product_by_id(created.id, custom_path=self.db_path)
        self.assertIsNotNone(by_id)
        self.assertEqual(by_id.name, "Soldering Station")

        by_sku = get_product_by_product_id("SKU-2002", custom_path=self.db_path)
        self.assertIsNotNone(by_sku)
        self.assertEqual(by_sku.id, created.id)

        # Case-insensitive SKU lookup
        by_sku_lower = get_product_by_product_id("sku-2002", custom_path=self.db_path)
        self.assertIsNotNone(by_sku_lower)

        all_items = get_all_products(custom_path=self.db_path)
        self.assertEqual(len(all_items), 1)

    def test_03_product_updates(self) -> None:
        """Confirm product modification and updated_at modification."""
        prod = add_product(
            product_id="SKU-3003",
            name="Wire Stripper",
            category="Tools",
            supplier="Klein",
            quantity=15,
            price=19.95,
            custom_path=self.db_path,
        )

        updated = update_product(
            item_id=prod.id,
            product_id="SKU-3003-MOD",
            name="Heavy-Duty Wire Stripper",
            category="Hand Tools",
            supplier="Klein Tools Inc.",
            quantity=5,  # Should become Low Stock
            price=24.50,
            custom_path=self.db_path,
        )

        self.assertEqual(updated.product_id, "SKU-3003-MOD")
        self.assertEqual(updated.name, "Heavy-Duty Wire Stripper")
        self.assertEqual(updated.category, "Hand Tools")
        self.assertEqual(updated.supplier, "Klein Tools Inc.")
        self.assertEqual(updated.quantity, 5)
        self.assertEqual(updated.price, 24.50)
        self.assertEqual(updated.stock_status, "Low Stock")

    def test_04_product_deletion(self) -> None:
        """Confirm product deletion removes record from database."""
        prod = add_product(
            product_id="SKU-DEL",
            name="Temporary Item",
            category="Misc",
            supplier="Temp Supplier",
            quantity=10,
            price=5.00,
            custom_path=self.db_path,
        )

        del_result = delete_product(prod.id, custom_path=self.db_path)
        self.assertTrue(del_result)

        # Confirm non-existence
        retrieved = get_product_by_id(prod.id, custom_path=self.db_path)
        self.assertIsNone(retrieved)

        # Deleting non-existent product raises ValueError
        with self.assertRaises(ValueError):
            delete_product(9999, custom_path=self.db_path)

    def test_05_duplicate_product_id_rejection(self) -> None:
        """Confirm uniqueness constraint on Product ID / SKU."""
        add_product(
            product_id="SKU-UNIQUE",
            name="First Item",
            category="Category A",
            supplier="Supplier A",
            quantity=10,
            price=10.0,
            custom_path=self.db_path,
        )

        # Creation with duplicate SKU (case-insensitive) must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            add_product(
                product_id="sku-unique",
                name="Second Item",
                category="Category B",
                supplier="Supplier B",
                quantity=20,
                price=15.0,
                custom_path=self.db_path,
            )
        self.assertIn("already exists", str(ctx.exception).lower())

        # Update collision: editing an item to take another item's SKU must fail
        second = add_product(
            product_id="SKU-SECOND",
            name="Second Item",
            category="Category B",
            supplier="Supplier B",
            quantity=20,
            price=15.0,
            custom_path=self.db_path,
        )

        with self.assertRaises(ValueError):
            update_product(
                item_id=second.id,
                product_id="SKU-UNIQUE",
                name="Second Item",
                category="Category B",
                supplier="Supplier B",
                quantity=20,
                price=15.0,
                custom_path=self.db_path,
            )

    def test_06_non_negative_quantity_and_price_validation(self) -> None:
        """Confirm validation prevents negative quantities or prices."""
        # Negative quantity
        with self.assertRaises(ValueError) as ctx:
            add_product("SKU-NEG-Q", "Negative Qty", "Cat", "Sup", -5, 10.0, custom_path=self.db_path)
        self.assertIn("negative", str(ctx.exception).lower())

        # Negative price
        with self.assertRaises(ValueError) as ctx:
            add_product("SKU-NEG-P", "Negative Price", "Cat", "Sup", 5, -10.0, custom_path=self.db_path)
        self.assertIn("negative", str(ctx.exception).lower())

        # Non-numeric input
        with self.assertRaises(ValueError):
            add_product("SKU-BAD-Q", "Bad Qty", "Cat", "Sup", "not_a_number", 10.0, custom_path=self.db_path)

        with self.assertRaises(ValueError):
            add_product("SKU-BAD-P", "Bad Price", "Cat", "Sup", 10, "free", custom_path=self.db_path)

    def test_07_empty_required_fields_rejection(self) -> None:
        """Confirm empty strings for required attributes are rejected."""
        cases = [
            ("", "Name", "Cat", "Sup", 1, 1.0),
            ("SKU", "", "Cat", "Sup", 1, 1.0),
            ("SKU", "Name", "", "Sup", 1, 1.0),
            ("SKU", "Name", "Cat", "", 1, 1.0),
        ]
        for sku, name, cat, sup, qty, pr in cases:
            with self.assertRaises(ValueError):
                add_product(sku, name, cat, sup, qty, pr, custom_path=self.db_path)

    def test_08_stock_status_computation(self) -> None:
        """Confirm smart calculation of Stock Status based on quantities."""
        # 0 -> Out of Stock
        self.assertEqual(determine_stock_status(0), "Out of Stock")
        self.assertEqual(determine_stock_status(-2), "Out of Stock")

        # 1..10 -> Low Stock
        self.assertEqual(determine_stock_status(1), "Low Stock")
        self.assertEqual(determine_stock_status(10), "Low Stock")

        # > 10 -> In Stock
        self.assertEqual(determine_stock_status(11), "In Stock")
        self.assertEqual(determine_stock_status(500), "In Stock")

    def test_09_database_persistence_across_reopen(self) -> None:
        """Confirm records persist across database closing and reopen (simulated restart)."""
        add_product("SKU-P1", "Persistent Item 1", "Hardware", "Acme", 50, 12.50, custom_path=self.db_path)
        add_product("SKU-P2", "Persistent Item 2", "Hardware", "Acme", 5, 25.00, custom_path=self.db_path)

        # Re-initialize schema to simulate restart
        status = init_database(self.db_path)
        self.assertTrue(status["existed_before"])

        items = get_all_products(custom_path=self.db_path)
        self.assertEqual(len(items), 2)
        skus = {item.product_id for item in items}
        self.assertIn("SKU-P1", skus)
        self.assertIn("SKU-P2", skus)

    def test_10_dashboard_statistics_from_actual_records(self) -> None:
        """Confirm dashboard statistics reflect true SQLite aggregate calculations."""
        # Baseline empty
        empty_stats = get_inventory_statistics(custom_path=self.db_path)
        self.assertEqual(empty_stats["total_products"], 0)
        self.assertEqual(empty_stats["total_quantity"], 0)
        self.assertEqual(empty_stats["total_value"], 0.0)
        self.assertEqual(empty_stats["low_stock_count"], 0)
        self.assertEqual(empty_stats["out_of_stock_count"], 0)

        # Add products across statuses
        # 1. In Stock (qty=50, price=10) -> value=500
        p1 = add_product("SKU-S1", "Normal Stock Item", "Electronics", "SupA", 50, 10.0, custom_path=self.db_path)
        # 2. Low Stock (qty=4, price=25) -> value=100
        p2 = add_product("SKU-S2", "Low Stock Item", "Tools", "SupB", 4, 25.0, custom_path=self.db_path)
        # 3. Out of Stock (qty=0, price=50) -> value=0
        p3 = add_product("SKU-S3", "Depleted Item", "Electronics", "SupA", 0, 50.0, custom_path=self.db_path)

        stats = get_inventory_statistics(custom_path=self.db_path)
        self.assertEqual(stats["total_products"], 3)
        self.assertEqual(stats["total_quantity"], 54)  # 50 + 4 + 0
        self.assertEqual(stats["total_value"], 600.0)  # 500 + 100 + 0
        self.assertEqual(stats["low_stock_count"], 1)
        self.assertEqual(stats["out_of_stock_count"], 1)
        self.assertEqual(stats["total_categories"], 2)  # Electronics, Tools

        # Delete an item and verify stats update immediately
        delete_product(p1.id, custom_path=self.db_path)
        updated_stats = get_inventory_statistics(custom_path=self.db_path)
        self.assertEqual(updated_stats["total_products"], 2)
        self.assertEqual(updated_stats["total_quantity"], 4)
        self.assertEqual(updated_stats["total_value"], 100.0)

    def test_11_dashboard_quick_search(self) -> None:
        """Confirm quick-search retrieves matching items across SKU, Name, Category, Supplier."""
        add_product("SKU-Q1", "Oscilloscope 100MHz", "Lab Equipment", "Rigol", 5, 299.0, custom_path=self.db_path)
        add_product("SKU-Q2", "Logic Analyzer", "Lab Equipment", "Saleae", 12, 199.0, custom_path=self.db_path)
        add_product("SKU-Q3", "Benchtop Power Supply", "Power", "Korad", 8, 89.0, custom_path=self.db_path)

        # Match by name
        res_name = search_products_quick("Oscilloscope", custom_path=self.db_path)
        self.assertEqual(len(res_name), 1)
        self.assertEqual(res_name[0].product_id, "SKU-Q1")

        # Match by category
        res_cat = search_products_quick("Lab Equipment", custom_path=self.db_path)
        self.assertEqual(len(res_cat), 2)

        # Match by supplier
        res_sup = search_products_quick("Korad", custom_path=self.db_path)
        self.assertEqual(len(res_sup), 1)
        self.assertEqual(res_sup[0].name, "Benchtop Power Supply")

        # Match by SKU
        res_sku = search_products_quick("SKU-Q2", custom_path=self.db_path)
        self.assertEqual(len(res_sku), 1)
        self.assertEqual(res_sku[0].name, "Logic Analyzer")

        # No match
        res_empty = search_products_quick("NonExistentItem999", custom_path=self.db_path)
        self.assertEqual(len(res_empty), 0)


if __name__ == "__main__":
    unittest.main()
