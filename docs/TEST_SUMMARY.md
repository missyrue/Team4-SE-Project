# Test Summary Report (STP deliverable)

**Project:** Online Bookstore System · **Test plan:** STP v1.0 · **Run:** pytest on Python 3.12 (GitHub Actions) / 3.13 (local)

> Numbers from the final run on `main` after the last merge. The detailed reports are in this folder: UNIT_TEST_REPORT.md, SYSTEM_VALIDATION_REPORT.md, CODE_COVERAGE_REPORT.md, BRANCH_COVERAGE_REPORT.md.

## Result

| Metric (STP §14) | Value |
|---|---|
| Test cases executed | 174 of 174 (100%) |
| Passed / failed | 174 / 0 |
| Line coverage of `app/` | 96% (branch 89%) |
| Open critical defects | 0 |
| Requirement coverage | all 26 functional, 5 of 6 security and 3 of 6 non-functional requirements are automated; the other 4 (NF-002, NF-003, NF-005, SR-004) are manual or deployment checks, see DEVIATIONS.md and TRACEABILITY.md |

## By file

| File | Level | Author | Tests |
|---|---|---|---|
| `tests/integration/test_admin_api.py` | Integration | Aditya | 39 |
| `tests/integration/test_auth_api.py` | Integration | Aanya | 15 |
| `tests/integration/test_cart_api.py` | Integration | Aaruni | 15 |
| `tests/integration/test_catalogue_api.py` | Integration | Aditya | 16 |
| `tests/integration/test_checkout_orders_api.py` | Integration | Aaruni | 37 |
| `tests/integration/test_end_to_end_flow.py` | System (end-to-end) | Aditya | 2 |
| `tests/integration/test_scale_performance.py` | Non-functional | Aanya | 2 |
| `tests/test_smoke.py` | Smoke | Aaruni | 2 |
| `tests/unit/test_catalogue_helpers.py` | Unit | Aditya | 5 |
| `tests/unit/test_inventory_service.py` | Unit | Aanya | 21 |
| `tests/unit/test_passwords.py` | Unit | Aanya | 6 |
| `tests/unit/test_payment_signature.py` | Unit | Aaruni | 4 |
| `tests/unit/test_pricing.py` | Unit | Aaruni | 10 |
| **Total** | | | **174** |

## Notes

* TC-Perf-01 / TC-Scale-01 ran against 10,000 seeded books with 20 concurrent threads; p90 response time was far below the 3 s target.
* Manual / not automated: TC-UX-01, TC-UX-02 (usability), TC-Sec-04 (TLS at deployment), TC-Reliability-01 (30-day availability). See DEVIATIONS.md section C.
* Defects found while testing (all fixed): payment-callback `401` was treated by the UI as "session expired" and logged the customer out; test fixture started the real database on import.
