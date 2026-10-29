# BBAT104 Review 2 Readiness Checklist — Inventory Management System (IMS)

**Course:** BBAT104 – Fundamentals of Total Quality Management  
**Academic Session:** 2026–27  
**Student Name:** Lokesh Paneru  
**Roll Number:** 2410303003  
**Section:** C  
**Quality Goal:** Q13 – Faster Search & Retrieval  
**Evaluation Milestone:** Review 2 (Base System & Assigned Quality Goal)  
**Date of Audit:** October 29, 2026  
**Audit Status:** **100% READY (All 16 SRS Acceptance Criteria & Review 2 Mandatory Targets Verified)**

---

## 1. Executive Summary

This audit checklist systematically verifies the **Inventory Management System (IMS)** against the **BBAT104 TQM Project Guidelines** and **SRS.md (Sections 19 & 21)**. 

All mandatory features for Review 2—including base CRUD operations, local salted PBKDF2 authentication, persistent SQLite storage, standalone installer packaging, and the complete Q13 quality suite (organized across **five implemented feature areas**)—have been fully validated through automated test suites and runtime GUI verification.

---

## 2. Review 2 Mandatory Requirements Matrix

| ID | Mandatory Requirement | Verification Method | Evidence Location | Status |
|:---|:---|:---|:---|:---:|
| **R2-01** | **Functional CRUD Modules**<br>Add, view, edit, and delete products with non-negative validation, SKU format checks, and duplicate SKU rejection. | Automated unit tests & modal UI interaction | [`app/inventory/crud.py`](../app/inventory/crud.py)<br>[`app/ui/views_inventory.py`](../app/ui/views_inventory.py)<br>[`app/ui/dialogs_inventory.py`](../app/ui/dialogs_inventory.py)<br>[`tests/test_inventory_crud.py`](../tests/test_inventory_crud.py) | **VERIFIED** |
| **R2-02** | **Working Authentication & Security**<br>First-run detection, salted PBKDF2 hashing (100,000 iterations), session tokens, Keep Me Logged In, and profile updates. | Automated unit tests & auth GUI flow | [`app/authentication/`](../app/authentication/)<br>[`app/ui/views_auth.py`](../app/ui/views_auth.py)<br>[`tests/test_authentication.py`](../tests/test_authentication.py)<br>[`docs/authentication.md`](../docs/authentication.md) | **VERIFIED** |
| **R2-03** | **Working Dashboard (Feature 1)**<br>Personalized greeting, store identity banner, real-time aggregate KPI metrics (total items, quantity, valuation, low stock, out of stock), and interactive deep links. | Automated unit tests & dashboard render inspection | [`app/dashboard/dashboard.py`](../app/dashboard/dashboard.py)<br>[`tests/test_inventory_crud.py`](../tests/test_inventory_crud.py)<br>[`tests/test_deeplinks_and_theme.py`](../tests/test_deeplinks_and_theme.py) | **VERIFIED** |
| **R2-04** | **Working Dashboard Quick-Search (Feature 2)**<br>Real-time keyword search across SKU, Name, Category, and Supplier with one-click reset and "Open in Inventory" bridge. | Automated search tests & GUI quick-search entry | [`app/inventory/search.py`](../app/inventory/search.py)<br>[`app/dashboard/dashboard.py`](../app/dashboard/dashboard.py)<br>[`tests/test_q13_search_retrieval.py`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-05** | **Working Search Filters (Feature 3)**<br>Multi-attribute composable filtering by Category, Supplier, Stock Status, and text query with conjunctive `AND` semantics. | Automated filter logic tests & dynamic dropdown checks | [`app/inventory/filters.py`](../app/inventory/filters.py)<br>[`tests/test_q13_search_retrieval.py`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-06** | **Working Sorting Options (Feature 4)**<br>Ascending and descending sorting across all 9 supported product columns using a strict whitelist. | Automated whitelist validation & SQL order checks | [`app/inventory/sorting.py`](../app/inventory/sorting.py)<br>[`tests/test_q13_search_retrieval.py`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-07** | **Database Query Optimization (Feature 5)**<br>Strategic B-tree indexes (`idx_products_product_id`, `idx_products_cat_sup`, etc.) verified via `EXPLAIN QUERY PLAN`. | SQLite query plan inspection & parameterized SQL check | [`app/database/schema.py`](../app/database/schema.py)<br>[`tests/test_database.py`](../tests/test_database.py)<br>[`tests/test_q13_search_retrieval.py`](../tests/test_q13_search_retrieval.py) | **VERIFIED** |
| **R2-08** | **Working SQLite Persistence**<br>Local SQLite storage (`ims.db`), WAL mode, foreign keys, transaction rollback on failure, survives app restart. | Automated unit tests closing & reopening DB connections | [`app/database/connection.py`](../app/database/connection.py)<br>[`app/database/schema.py`](../app/database/schema.py)<br>[`tests/test_database.py`](../tests/test_database.py)<br>[`docs/database_design.md`](../docs/database_design.md) | **VERIFIED** |
| **R2-09** | **Demonstrable Q13 Performance Benchmarks**<br>Repeatable empirical benchmarking on 1,000, 10,000, and 50,000 rows demonstrating up to 3.74x speedup. | Standalone benchmark script execution & latency logging | [`run_benchmark.py`](../run_benchmark.py)<br>[`docs/search_and_performance.md`](../docs/search_and_performance.md) | **VERIFIED** |
| **R2-10** | **Danger Zone & In-App Reset**<br>Password-confirmed account deletion, wiping all products, users, and session settings, restarting into setup wizard. | Automated unit tests & modal UI flow | [`app/settings/settings.py`](../app/settings/settings.py)<br>[`app/ui/views_settings.py`](../app/ui/views_settings.py)<br>[`tests/test_account_deletion_and_setup.py`](../tests/test_account_deletion_and_setup.py) | **VERIFIED** |
| **R2-11** | **Standalone Windows Packaging**<br>Automated PyInstaller and Inno Setup 6 pipeline producing `setup.exe` (22.06 MB) with data retention prompts. | Compiler output & installer inspection | [`build_installer.py`](../build_installer.py)<br>[`installer.iss`](../installer.iss)<br>[`setup.exe`](../setup.exe) | **VERIFIED** |

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
| 11 | Dashboard Overview & Real-Time Stock Statistics work with live calculations (FR-15). | [`app/dashboard/dashboard.py`](../app/dashboard/dashboard.py) | `test_01_view_caching_across_navigation` | **PASS** |
| 12 | Dashboard Quick-Search rapidly retrieves records across 4 fields (FR-16). | [`app/inventory/search.py`](../app/inventory/search.py) | `test_11_dashboard_quick_search` | **PASS** |
| 13 | Search Filters work composably with instant clear (FR-17). | [`app/inventory/filters.py`](../app/inventory/filters.py) | `test_02_combined_search_filters` | **PASS** |
| 14 | Sorting Options sort all supported columns ascending and descending (FR-18). | [`app/inventory/sorting.py`](../app/inventory/sorting.py) | `test_05_ascending_and_descending_sorting` | **PASS** |
| 15 | Database Query Optimization and parameterized SQL are verified via benchmark (FR-19, FR-20). | [`app/database/schema.py`](../app/database/schema.py), [`run_benchmark.py`](../run_benchmark.py) | `test_08_query_plan_index_utilization` | **PASS** |
| 16 | The application operates completely offline with standalone installer and 100% test pass rate. | Entire system | Zero remote dependencies, 55 passing tests | **PASS** |

---

## 4. Test Execution Summary

- **Total Automated Unit Tests:** 55
- **Passed:** 55 (100%)
- **Failed:** 0
- **Errors:** 0
- **Test Suites (8 Suites):**
  1. `test_account_deletion_and_setup.py`: 4 tests
  2. `test_authentication.py`: 12 tests
  3. `test_database.py`: 5 tests
  4. `test_deeplinks_and_theme.py`: 5 tests
  5. `test_inventory_crud.py`: 10 tests
  6. `test_modal_navigation_and_layout.py`: 7 tests
  7. `test_q13_search_retrieval.py`: 8 tests
  8. `test_transition_and_view_caching.py`: 4 tests
- **Log Location:** [`docs/review2/test-results.txt`](test-results.txt)

---

## 5. Scope Boundary Compliance

| Phase / Component | BBAT104 Guideline Scope | Current Status in IMS |
|:---|:---|:---:|
| **Review 1** | SRS, Scope, Architecture, Git Setup | **Completed & Verified** |
| **Review 2** | Base CRUD, Auth, Dashboard, Q13 Search/Sort/Filter/Indexes, Packaging | **Completed & Verified** |
| **Review 3** | FMEA, Quality Tools, SQC Charts (Pareto / Fishbone / Control Charts) | **Planned for Review 3** (Intentionally deferred to Review 3 scope) |

---

## 6. Audit Conclusion

The application strictly complies with all requirements outlined for **Review 2**. All modules operate reliably offline, input constraints and transaction rollbacks prevent data corruption, the empirical Q13 benchmark provides solid academic quality evidence, and standalone Windows installer packaging (`setup.exe`) is completely realized.
