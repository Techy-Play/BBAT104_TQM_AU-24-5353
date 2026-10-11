"""Repeatable performance benchmarking utility for Q13 query optimization.

Generates deterministic synthetic datasets (1,000, 10,000, 50,000 products)
in isolated temporary databases to measure and compare query latency:
- Indexed queries (with Q13 SQLite B-tree indexes)
- Unindexed queries (indexes dropped to establish baseline)
- Query plan inspection via EXPLAIN QUERY PLAN
"""

from __future__ import annotations

import logging
import random
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.database.connection import create_connection
from app.database.schema import (
    CREATE_INDEXES_SQL,
    CREATE_TABLES_SQL,
    CREATE_TRIGGERS_SQL,
)

logger = logging.getLogger(__name__)

# Fixed random seed for 100% reproducible benchmark datasets
BENCHMARK_SEED = 42

CATEGORIES = [
    "Electronics",
    "Hardware",
    "Tools",
    "Power Systems",
    "Measurement",
    "Sensors",
    "Cables & Wiring",
    "Robotics",
    "Fasteners",
    "Storage",
]

SUPPLIERS = [
    "Apex Tech Ltd",
    "Global Parts Co",
    "Precision Instruments",
    "Omega Dynamics",
    "Summit Industrial",
    "Delta Electronics",
    "Prime Hardware Inc",
    "Vanguard Supplies",
    "NextGen Logistics",
    "Pioneer Components",
]

ADJECTIVES = ["Precision", "Industrial", "Heavy-Duty", "Compact", "High-Voltage", "Standard", "Digital", "Pro"]
NOUNS = ["Multimeter", "Sensor Module", "Power Supply", "Connector", "Cable 2m", "Clamp Meter", "Controller", "Relay 12V"]


@dataclass
class BenchmarkResult:
    """Stores the execution timings of a single benchmark test."""

    dataset_size: int
    query_name: str
    sql: str
    params: Tuple[Any, ...]
    repetitions: int
    indexed_time_ms: float
    unindexed_time_ms: float
    indexed_query_plan: str
    unindexed_query_plan: str

    @property
    def speedup(self) -> float:
        """Calculate acceleration factor from indexing."""
        if self.indexed_time_ms <= 0:
            return 1.0
        return round(self.unindexed_time_ms / self.indexed_time_ms, 2)


def generate_synthetic_products(count: int, seed: int = BENCHMARK_SEED) -> List[Tuple]:
    """Generate reproducible synthetic product tuples for fast batch insertion."""
    rng = random.Random(seed)
    records = []

    for i in range(1, count + 1):
        sku = f"SKU-{i:06d}"
        adj = rng.choice(ADJECTIVES)
        noun = rng.choice(NOUNS)
        name = f"{adj} {noun} #{i}"
        category = rng.choice(CATEGORIES)
        supplier = rng.choice(SUPPLIERS)
        qty = rng.randint(0, 150)
        price = round(rng.uniform(2.50, 499.00), 2)

        if qty == 0:
            status = "Out of Stock"
        elif qty <= 10:
            status = "Low Stock"
        else:
            status = "In Stock"

        records.append((sku, name, category, supplier, qty, price, status))

    return records


def setup_benchmark_database(db_path: Path, count: int) -> None:
    """Initialize test database and populate with synthetic products in a single transaction."""
    conn = create_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.executescript(CREATE_TABLES_SQL)
            cursor.executescript(CREATE_INDEXES_SQL)
            cursor.executescript(CREATE_TRIGGERS_SQL)

            records = generate_synthetic_products(count)
            cursor.executemany(
                """
                INSERT INTO products (product_id, name, category, supplier, quantity, price, stock_status)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                records,
            )
    finally:
        conn.close()


def drop_q13_indexes(conn: sqlite3.Connection) -> None:
    """Drop Q13 search and filter indexes to establish an unindexed baseline."""
    indexes_to_drop = [
        "idx_products_name",
        "idx_products_category",
        "idx_products_supplier",
        "idx_products_stock_status",
        "idx_products_cat_sup",
    ]
    cursor = conn.cursor()
    for idx in indexes_to_drop:
        cursor.execute(f"DROP INDEX IF EXISTS {idx};")
    conn.commit()


def get_query_plan(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...]) -> str:
    """Retrieve the SQLite EXPLAIN QUERY PLAN detail string."""
    cursor = conn.cursor()
    cursor.execute(f"EXPLAIN QUERY PLAN {sql}", params)
    rows = cursor.fetchall()
    return " | ".join(str(r["detail"]) for r in rows)


def measure_query_latency(
    conn: sqlite3.Connection,
    sql: str,
    params: Tuple[Any, ...],
    repetitions: int = 15,
) -> float:
    """Measure average query execution latency in milliseconds over multiple repetitions."""
    cursor = conn.cursor()

    # Warm-up run
    cursor.execute(sql, params)
    cursor.fetchall()

    start_time = time.perf_counter()
    for _ in range(repetitions):
        cursor.execute(sql, params)
        cursor.fetchall()
    total_time = time.perf_counter() - start_time

    return (total_time / repetitions) * 1000.0


def run_benchmark_for_size(
    dataset_size: int,
    repetitions: int = 20,
) -> List[BenchmarkResult]:
    """Execute repeatable benchmarks for a given dataset size comparing indexed vs unindexed."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / f"bench_{dataset_size}.db"
        setup_benchmark_database(db_path, dataset_size)

        benchmark_queries = [
            (
                "Exact SKU Lookup",
                "SELECT * FROM products WHERE product_id = ?;",
                ("SKU-000500",),
            ),
            (
                "Category Filter",
                "SELECT * FROM products WHERE category = ? COLLATE NOCASE;",
                ("Electronics",),
            ),
            (
                "Multi-Filter (Category + Supplier)",
                "SELECT * FROM products WHERE category = ? COLLATE NOCASE AND supplier = ? COLLATE NOCASE;",
                ("Hardware", "Apex Tech Ltd"),
            ),
            (
                "Stock Status Filter",
                "SELECT * FROM products WHERE stock_status = ?;",
                ("Low Stock",),
            ),
            (
                "Prefix Search (SKU)",
                "SELECT * FROM products WHERE product_id LIKE ?;",
                ("SKU-001%",),
            ),
            (
                "Substring Search (Arbitrary)",
                "SELECT * FROM products WHERE name LIKE ?;",
                ("%Multimeter%",),
            ),
            (
                "Whitelist Sort (Price ASC)",
                "SELECT * FROM products ORDER BY price ASC, id ASC LIMIT 50;",
                (),
            ),
        ]

        results: List[BenchmarkResult] = []

        # 1. Run WITH Q13 Indexes
        conn_indexed = create_connection(db_path)
        indexed_timings = {}
        indexed_plans = {}
        try:
            for q_name, sql, params in benchmark_queries:
                t = measure_query_latency(conn_indexed, sql, params, repetitions=repetitions)
                plan = get_query_plan(conn_indexed, sql, params)
                indexed_timings[q_name] = t
                indexed_plans[q_name] = plan
        finally:
            conn_indexed.close()

        # 2. Drop non-primary indexes to establish unindexed baseline
        conn_unindexed = create_connection(db_path)
        try:
            drop_q13_indexes(conn_unindexed)
            for q_name, sql, params in benchmark_queries:
                t = measure_query_latency(conn_unindexed, sql, params, repetitions=repetitions)
                plan = get_query_plan(conn_unindexed, sql, params)

                results.append(
                    BenchmarkResult(
                        dataset_size=dataset_size,
                        query_name=q_name,
                        sql=sql,
                        params=params,
                        repetitions=repetitions,
                        indexed_time_ms=round(indexed_timings[q_name], 3),
                        unindexed_time_ms=round(t, 3),
                        indexed_query_plan=indexed_plans[q_name],
                        unindexed_query_plan=plan,
                    )
                )
        finally:
            conn_unindexed.close()

        return results


def run_full_q13_benchmark(
    sizes: Tuple[int, ...] = (1_000, 10_000, 50_000),
    repetitions: int = 15,
) -> Dict[int, List[BenchmarkResult]]:
    """Execute complete multi-dataset benchmark suite."""
    all_results: Dict[int, List[BenchmarkResult]] = {}
    for size in sizes:
        logger.info("Executing benchmark for N = %d records (%d repetitions)...", size, repetitions)
        all_results[size] = run_benchmark_for_size(size, repetitions=repetitions)
    return all_results
