# BBAT104 Review 2 Readiness Checklist — Inventory Management System (IMS)

**Course:** BBAT104 – Fundamentals of Total Quality Management  
**Quality Goal:** Q13 – Faster Search & Retrieval  
**Evaluation Milestone:** Review 2 (Base System & Assigned Quality Goal)  
**Date of Audit:** October 11, 2026  
**Audit Status:** **100% READY (All 16 SRS Acceptance Criteria & Review 2 Targets Verified)**

---

## 1. Executive Summary

This audit checklist systematically verifies the **Inventory Management System (IMS)** against the **BBAT104 TQM Project Guidelines** and **SRS.md (Sections 19 & 21)**. All mandatory features for Review 2—including core CRUD operations, multi-layered authentication, real-time dashboard analytics, persistent SQLite storage, and the complete Q13 quality suite (quick-search, composable filtering, whitelisted sorting, query indexing, and empirical benchmarks)—have been validated via automated test suites and runtime GUI interaction.

---

## 2. Review 2 Mandatory Requirements Matrix

| ID | Mandatory Requirement | Verification Method | Evidence Location | Status |
|:---|:---|:---|:---|:---:|
| **R2-01** | **Functional CRUD Modules**<br>Add, view, edit, and delete products with non-negative validation and unique SKU checks. | Automated unit tests & modal UI interaction | [`app/inventory/crud.py`](../app/inventory/crud.py)<br>[`app/ui/views_inventory.py`](../app/ui/views_inventory.py)<br>[`app/ui/dialogs_inventory.py`](../app/ui/dialogs_inventory.py)<br>[`tests/test_inventory_crud.py`](../tests/test_inventory_crud.py) | **VERIFIED** |
| **R2-02** | **Working Authentication & Security**<br>First-run detection, salted PBKDF2 hashing (100,000 iterations), session tokens, Keep Me Logged In, and profile updates. | Automated unit tests & auth GUI flow | [`app/authentication/`](../app/authentication/)<br>[`app/ui/views_auth.py`](../app/ui/views_auth.py)<br>[`tests/test_authentication.py`](../tests/test_authentication.py)<br>[`docs/authentication.md`](../docs/authentication.md) | **VERIFIED** |
| **R2-03** | **Working Dashboard**<br>Personalized greeting, dynamic store banner, real-time SQLite aggregate metrics (total items, quantity, low stock, out of stock, valuation). | Automated unit tests & dashboard render inspection | [`app/dashboard/dashboard.py`](../app/dashboard/dashboard.py)<br>[`tests/test_inventory_crud.py#test_10`](../tests/test_inventory_crud.py) | **VERIFIED** |
| **R2-04** | **Working SQLite Persistence**<br>Local SQLite storage (`ims.db`), WAL mode, foreign keys, transaction rollback on failure, survives app restart. | Automated unit tests closing & reopening DB connections | [`app/database/connection.py`](../app/database/connection.py)<br>[`app/database/schema.py`](../app/database/schema.py)<br>[`tests/test_database.py`](../tests/test_database.py)<br>[`docs/database_design.md`](../docs/database_design.md) | **VERIFIED** |
| **R2-05** | **Working Search Filters (Q13)**<br>Multi-attribute composable filtering by Category, Supplier, Stock Status, and text query with `AND` semantics. | Automated filter logic tests & dynamic dropdown checks | [`app/inventory/filters.py`](../app/inventory/filters.py)<br>[`tests/test_q13_search_retrieval.py`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-06** | **Working Sorting Options (Q13)**<br>Ascending and descending sorting across all 8 supported product columns using a strict whitelist. | Automated whitelist validation & SQL order checks | [`app/inventory/sorting.py`](../app/inventory/sorting.py)<br>[`tests/test_q13_search_retrieval.py`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-07** | **Working Dashboard Quick-Search (Q13)**<br>Real-time keyword search across SKU, Name, Category, and Supplier with one-click reset. | Automated search tests & GUI quick-search entry | [`app/inventory/search.py`](../app/inventory/search.py)<br>[`app/dashboard/dashboard.py`](../app/dashboard/dashboard.py)<br>[`tests/test_q13_search_retrieval.py`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-08** | **Database Query Optimization (Q13)**<br>Strategic B-tree indexes (`idx_products_product_id`, `idx_products_cat_sup`, etc.) verified via `EXPLAIN QUERY PLAN`. | SQLite query plan inspection & parameterized SQL check | [`app/database/schema.py`](../app/database/schema.py)<br>[`tests/test_database.py#test_q13`](../tests/test_database.py)<br>[`tests/test_q13_search_retrieval.py#test_08`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-09** | **Demonstrable Q13 Performance Benchmarks**<br>Repeatable empirical benchmarking on 1,000, 10,000, and 50,000 rows demonstrating up to 4.26x speedup. | Standalone benchmark script execution & latency logging | [`run_benchmark.py`](../run_benchmark.py)<br>[`docs/search_and_performance.md`](../docs/search_and_performance.md) | **VERIFIED** |

---

## 3. SRS Section 19 Acceptance Criteria Audit

| # | Acceptance Criterion (SRS-19) | Implementation Module | Evidence / Test Case | Result |
|:---:|:---|:---|:---|:---:|
| 1 | The application launches successfully. | [`app/main.py`](../app/main.py), [`run.py`](../run.py) | `IMSApplication` bootstrap test passed | **PASS** |
| 2 | First-time users can create an account. | [`app/authentication/setup.py`](../app/authentication/setup.py) | `test_01_first_user_creation` | **PASS** |
| 3 | Existing users can authenticate using password. | [`app/authentication/login.py`](../app/authentication/login.py) | `test_04_correct_password_verification` | **PASS** |
| 4 | Keep Me Logged In works as specified. | [`app/authentication/login.py`](../app/authentication/login.py) | `test_08_keep_me_logged_in_behavior` | **PASS** |
| 5 | Preference can be changed through Settings. | [`app/ui/views_settings.py`](../app/ui/views_settings.py) | `test_11_user_profile_retrieval_and_update` | **PASS** |
| 6 | Inventory records can be created. | [`app/inventory/crud.py`](../app/inventory/crud.py) | `test_01_product_creation` | **PASS** |
| 7 | Inventory records can be viewed. | [`app/inventory/crud.py`](../app/inventory/crud.py) | `test_02_product_retrieval` | **PASS** |
| 8 | Inventory records can be updated. | [`app/inventory/crud.py`](../app/inventory/crud.py) | `test_03_product_updates` | **PASS** |
| 9 | Inventory records can be deleted. | [`app/inventory/crud.py`](../app/inventory/crud.py) | `test_04_product_deletion` | **PASS** |
| 10 | Inventory data persists after restart. | [`app/database/connection.py`](../app/database/connection.py) | `test_09_database_persistence_across_reopen` | **PASS** |
| 11 | Dashboard Quick-Search works. | [`app/inventory/search.py`](../app/inventory/search.py) | `test_11_dashboard_quick_search` | **PASS** |
| 12 | Search Filters work together. | [`app/inventory/filters.py`](../app/inventory/filters.py) | `test_02_combined_search_filters` | **PASS** |
| 13 | Sorting Options work in ASC and DESC. | [`app/inventory/sorting.py`](../app/inventory/sorting.py) | `test_05_ascending_and_descending_sorting` | **PASS** |
| 14 | Parameterized SQLite queries used for retrieval. | [`app/database/queries.py`](../app/database/queries.py) | `test_07_safe_parameterized_queries` | **PASS** |
| 15 | Database optimization can be demonstrated. | [`run_benchmark.py`](../run_benchmark.py) | `test_08_query_plan_index_utilization` | **PASS** |
| 16 | The application operates completely offline. | Entire system | Zero remote/network network dependencies | **PASS** |

---

## 4. Test Execution Summary

- **Total Automated Unit Tests:** 36
- **Passed:** 36 (100%)
- **Failed:** 0
- **Errors:** 0
- **Duration:** 3.035 seconds
- **Log Location:** [`docs/review2/test-results.txt`](test-results.txt)

---

## 5. Scope Boundary Compliance

| Phase / Component | BBAT104 Guideline Scope | Current Status in IMS |
|:---|:---|:---:|
| **Review 1** | SRS, Scope, Architecture, Git Setup | **Completed & Verified** |
| **Review 2** | Base CRUD, Auth, Dashboard, Q13 Search/Sort/Filter/Indexes | **Completed & Verified** |
| **Review 3** | FMEA, Quality Tools, SQC Charts (Pareto / Fishbone / Control Charts) | **Planned for Review 3** (Not Started as per scope) |
| **Final Packaging** | Windows Executable (`.exe`) via PyInstaller | **Planned for Final Review** |

---

## 6. Audit Conclusion

The application strictly complies with all requirements outlined for **Review 2**. All modules operate reliably offline, input constraints and transaction rollbacks prevent data corruption, and the empirical Q13 benchmark provides solid academic quality evidence for presentation.
