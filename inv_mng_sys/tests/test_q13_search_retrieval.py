"""Automated tests for Q13 (Faster Search & Retrieval).

Validates:
1. Quick-search retrieval across each supported field (product_id, name, category, supplier).
2. Combined multi-criteria search filters working together.
3. Empty result handling and clearing filters back to full inventory.
4. Ascending and descending sorting for all whitelisted columns.
5. Strict whitelist rejection of unauthorized sort columns and directions.
6. Parameterized SQL safety against special characters and SQL injection attempts.
7. SQLite EXPLAIN QUERY PLAN index utilization verification.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from app.database.queries import explain_query_plan
from app.database.schema import init_database
from app.inventory.crud import add_product
from app.inventory.filters import (
    FilterCriteria,
    filter_products,
    get_distinct_categories,
    get_distinct_suppliers,
)
from app.inventory.search import search_products_quick
from app.inventory.sorting import (
    SORT_COLUMN_WHITELIST,
    build_order_by_clause,
    sanitize_sort_column,
    sanitize_sort_direction,
)


class TestQ13SearchAndRetrieval(unittest.TestCase):
    """Test suite for Q13 search, filtering, whitelist sorting, and query optimization."""

    def setUp(self) -> None:
        """Create an isolated test database with a diverse sample inventory."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_q13.db"
        init_database(self.db_path)

        # Seed sample inventory covering diverse categories, suppliers, quantities, and prices
        self.items = [
            add_product("SKU-101", "Digital Multimeter 6000", "Electronics", "Apex Instruments", 20, 59.99, custom_path=self.db_path),
            add_product("SKU-102", "Oscilloscope Probe 100MHz", "Electronics", "Rigol Technologies", 8, 29.50, custom_path=self.db_path),
            add_product("SKU-201", "Heavy-Duty Cable Cutter", "Tools", "Klein Tools", 15, 34.00, custom_path=self.db_path),
            add_product("SKU-202", "Precision Screwdriver Set", "Tools", "Apex Instruments", 5, 18.75, custom_path=self.db_path),
            add_product("SKU-301", "DC Power Supply 30V 5A", "Power Systems", "Rigol Technologies", 0, 149.00, custom_path=self.db_path),
            add_product("SKU-302", "Lithium Battery Pack 12V", "Power Systems", "Apex Instruments", 45, 89.90, custom_path=self.db_path),
        ]

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_search_by_each_supported_field(self) -> None:
        """Confirm quick-search retrieves matching items across all four target fields."""
        # 1. Match by Product ID (SKU)
        res_sku = search_products_quick("SKU-101", custom_path=self.db_path)
        self.assertEqual(len(res_sku), 1)
        self.assertEqual(res_sku[0].name, "Digital Multimeter 6000")

        # 2. Match by Product Name
        res_name = search_products_quick("Oscilloscope", custom_path=self.db_path)
        self.assertEqual(len(res_name), 1)
        self.assertEqual(res_name[0].product_id, "SKU-102")

        # 3. Match by Category
        res_cat = search_products_quick("Tools", custom_path=self.db_path)
        self.assertEqual(len(res_cat), 2)
        skus = {p.product_id for p in res_cat}
        self.assertEqual(skus, {"SKU-201", "SKU-202"})

        # 4. Match by Supplier
        res_sup = search_products_quick("Rigol", custom_path=self.db_path)
        self.assertEqual(len(res_sup), 2)
        skus = {p.product_id for p in res_sup}
        self.assertEqual(skus, {"SKU-102", "SKU-301"})

    def test_02_combined_search_filters(self) -> None:
        """Confirm multiple filters combine using AND logic."""
        # Category='Electronics' AND Supplier='Apex Instruments'
        criteria = FilterCriteria(
            category="Electronics",
            supplier="Apex Instruments",
        )
        results = filter_products(criteria, custom_path=self.db_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].product_id, "SKU-101")

        # Category='Power Systems' AND Stock Status='Out of Stock'
        crit_out = FilterCriteria(
            category="Power Systems",
            stock_status="Out of Stock",
        )
        results_out = filter_products(crit_out, custom_path=self.db_path)
        self.assertEqual(len(results_out), 1)
        self.assertEqual(results_out[0].product_id, "SKU-301")

        # Text search + Category + Supplier combined
        crit_triple = FilterCriteria(
            search_query="Precision",
            category="Tools",
            supplier="Apex Instruments",
        )
        results_triple = filter_products(crit_triple, custom_path=self.db_path)
        self.assertEqual(len(results_triple), 1)
        self.assertEqual(results_triple[0].product_id, "SKU-202")

    def test_03_empty_results_and_clearing_filters(self) -> None:
        """Confirm non-matching filters return empty list and clearing restores full list."""
        # Non-matching filter
        crit_empty = FilterCriteria(
            category="Electronics",
            stock_status="Out of Stock",  # No Electronics items are Out of Stock
        )
        results_empty = filter_products(crit_empty, custom_path=self.db_path)
        self.assertEqual(len(results_empty), 0)

        # Non-matching search text
        crit_no_text = FilterCriteria(search_query="NonExistentComponentX99")
        self.assertEqual(len(filter_products(crit_no_text, custom_path=self.db_path)), 0)

        # Clear / Default criteria restores all 6 seeded records
        crit_default = FilterCriteria()
        self.assertFalse(crit_default.is_filtered())
        results_all = filter_products(crit_default, custom_path=self.db_path)
        self.assertEqual(len(results_all), 6)

    def test_04_distinct_category_and_supplier_helpers(self) -> None:
        """Confirm dropdown helpers return correct distinct sorted values."""
        cats = get_distinct_categories(custom_path=self.db_path)
        self.assertEqual(cats, ["Electronics", "Power Systems", "Tools"])

        sups = get_distinct_suppliers(custom_path=self.db_path)
        self.assertEqual(sups, ["Apex Instruments", "Klein Tools", "Rigol Technologies"])

    def test_05_ascending_and_descending_sorting(self) -> None:
        """Confirm sorting works properly across all whitelisted columns in both directions."""
        columns = [
            "product_id",
            "name",
            "category",
            "supplier",
            "quantity",
            "price",
            "stock_status",
            "updated_at",
        ]

        for col in columns:
            # ASC
            crit_asc = FilterCriteria(sort_by=col, sort_direction="asc")
            res_asc = filter_products(crit_asc, custom_path=self.db_path)
            self.assertEqual(len(res_asc), 6)

            # DESC
            crit_desc = FilterCriteria(sort_by=col, sort_direction="desc")
            res_desc = filter_products(crit_desc, custom_path=self.db_path)
            self.assertEqual(len(res_desc), 6)

        # Explicit numerical order verification for Price
        res_price_asc = filter_products(FilterCriteria(sort_by="price", sort_direction="asc"), custom_path=self.db_path)
        prices = [p.price for p in res_price_asc]
        self.assertEqual(prices, sorted(prices))

        res_price_desc = filter_products(FilterCriteria(sort_by="price", sort_direction="desc"), custom_path=self.db_path)
        prices_desc = [p.price for p in res_price_desc]
        self.assertEqual(prices_desc, sorted(prices, reverse=True))

        # Explicit numerical order verification for Quantity
        res_qty_asc = filter_products(FilterCriteria(sort_by="quantity", sort_direction="asc"), custom_path=self.db_path)
        qtys = [p.quantity for p in res_qty_asc]
        self.assertEqual(qtys, sorted(qtys))

    def test_06_invalid_sort_rejection_and_whitelist(self) -> None:
        """Confirm arbitrary/injected sort columns and directions are rejected."""
        # SQL injection attempts in sort column
        bad_columns = [
            "id; DROP TABLE products;--",
            "password_hash",
            "nonexistent_column",
            "1=1",
            "name UNION SELECT * FROM users",
        ]
        for bad_col in bad_columns:
            with self.assertRaises(ValueError):
                sanitize_sort_column(bad_col)

            with self.assertRaises(ValueError):
                build_order_by_clause(sort_by=bad_col, direction="asc")

        # Invalid direction
        bad_dirs = ["sideways", "ASC; DROP TABLE products;", "RANDOM()"]
        for bad_dir in bad_dirs:
            with self.assertRaises(ValueError):
                sanitize_sort_direction(bad_dir)

    def test_07_safe_parameterized_queries(self) -> None:
        """Confirm search strings containing quotes and SQL metacharacters execute safely."""
        tricky_queries = [
            "'; DROP TABLE products; --",
            "Apex's Tools",
            '"quoted"',
            "1' OR '1'='1",
            "SKU-101'--",
        ]
        for query in tricky_queries:
            # Must execute without syntax errors or injection
            results = filter_products(FilterCriteria(search_query=query), custom_path=self.db_path)
            self.assertIsInstance(results, list)

        # Confirm products table was not dropped or corrupted
        all_prods = filter_products(FilterCriteria(), custom_path=self.db_path)
        self.assertEqual(len(all_prods), 6)

    def test_08_query_plan_index_utilization(self) -> None:
        """Verify SQLite query planner utilizes indexes for supported query patterns."""
        # 1. Exact SKU lookup uses unique index
        plan_sku = explain_query_plan(
            "SELECT * FROM products WHERE product_id = ?;",
            ("SKU-101",),
            custom_path=self.db_path,
        )
        plan_sku_str = " ".join(str(p["detail"]) for p in plan_sku)
        self.assertIn("USING INDEX idx_products_product_id", plan_sku_str)

        # 2. Combined Category + Supplier filter uses composite index idx_products_cat_sup
        plan_composite = explain_query_plan(
            "SELECT * FROM products WHERE category = ? COLLATE NOCASE AND supplier = ? COLLATE NOCASE;",
            ("Electronics", "Apex Instruments"),
            custom_path=self.db_path,
        )
        plan_comp_str = " ".join(str(p["detail"]) for p in plan_composite)
        self.assertIn("USING INDEX idx_products_cat_sup", plan_comp_str)

        # 3. Arbitrary substring search (%term%) uses SCAN TABLE (realistic B-tree behavior)
        plan_substr = explain_query_plan(
            "SELECT * FROM products WHERE name LIKE ?;",
            ("%Multimeter%",),
            custom_path=self.db_path,
        )
        plan_substr_str = " ".join(str(p["detail"]) for p in plan_substr)
        self.assertTrue(
            "SCAN" in plan_substr_str and "products" in plan_substr_str,
            f"Expected SCAN on products, got: {plan_substr_str}",
        )



if __name__ == "__main__":
    unittest.main()
