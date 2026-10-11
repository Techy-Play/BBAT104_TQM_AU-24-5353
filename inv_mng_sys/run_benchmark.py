"""CLI runner for Q13 Performance Benchmarking Suite.

Executes real SQLite latency tests on 1,000, 10,000, and 50,000 records
comparing indexed vs unindexed query execution times and printing
a markdown-formatted report.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.inventory.benchmark import run_full_q13_benchmark


def main() -> int:
    print("================================================================================")
    print("BBAT104 - Q13 FASTER SEARCH & RETRIEVAL: PERFORMANCE BENCHMARK SUITE")
    print("================================================================================")
    print("Testing realistic dataset sizes: 1,000, 10,000, and 50,000 products.")
    print("Data is generated in isolated temporary SQLite databases (production data unaffected).")
    print("Running benchmarks...")
    print()

    start_total = time.time()
    results_by_size = run_full_q13_benchmark(sizes=(1_000, 10_000, 50_000), repetitions=15)
    elapsed_total = time.time() - start_total

    for size, results in results_by_size.items():
        print(f"### Dataset Size: N = {size:,} Products")
        print("| Query Description | Unindexed (ms) | Indexed (ms) | Speedup | Query Plan (Indexed) |")
        print("|---|---|---|---|---|")
        for r in results:
            plan_summary = r.indexed_query_plan
            if "SCAN" in plan_summary:
                plan_badge = f"`SCAN TABLE`"
            elif "SEARCH" in plan_summary:
                plan_badge = f"`SEARCH USING INDEX`"
            else:
                plan_badge = f"`{plan_summary[:35]}...`"

            speedup_str = f"**{r.speedup}x**" if r.speedup > 1.0 else f"{r.speedup}x"
            print(f"| {r.query_name} | {r.unindexed_time_ms:.3f} ms | {r.indexed_time_ms:.3f} ms | {speedup_str} | {plan_badge} |")
        print()

    print(f"Benchmark completed successfully in {elapsed_total:.2f} seconds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
