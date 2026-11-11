# Requirements Traceability Matrix (updated after Sprint 1 + 2)

Status: **N** not started · **P** partially implemented / needs manual verification · **A** accepted (implemented + automated test passes)
Test names are the pytest functions; run `pytest -v` to see them.

## Functional requirements

| Req ID | Requirement | Code | Test case(s) | Automated tests in | Status |
|---|---|---|---|---|---|
| OBS-F-001 | Create account | `routers/auth.py` `register` | TC-Auth-01 | `tests/integration/test_auth_api.py` | A |
| OBS-F-002 | Login | `routers/auth.py` `login` | TC-Auth-02 | `test_auth_api.py` | A |
| OBS-F-003 | Logout | `routers/auth.py` `logout` | TC-Auth-03 | `test_auth_api.py` | A |
| OBS-F-004 | Display active books | `routers/catalogue.py` | TC-Cat-01 | `test_catalogue_api.py` | A |
| OBS-F-005 | Search title/author/ISBN | `catalogue.py` `search_books` | TC-Cat-02 | `test_catalogue_api.py` | A |
| OBS-F-006 | Filter category/price | `catalogue.py` `run_search` | TC-Cat-03 | `test_catalogue_api.py` | A |
| OBS-F-007 | Sort title/price | `catalogue.py` `SORT_ORDER` | TC-Cat-04 | `test_catalogue_api.py` | A |
| OBS-F-008 | Book detail | `catalogue.py` `book_detail` | TC-Book-01 | `test_catalogue_api.py` | A |
| OBS-F-009 | Add to cart | `routers/cart.py` `add_item` | TC-Cart-01 | `test_cart_api.py` | A |
| OBS-F-010 | Change/remove cart item | `cart.py` `update_item`, `remove_item` | TC-Cart-02 | `test_cart_api.py` | A |
| OBS-F-011 | Stock-aware quantity limit | `cart.py` `_check_stock` | TC-Cart-03 | `test_cart_api.py` | A |
| OBS-F-012 | Delivery details | `routers/orders.py` `CheckoutIn` | TC-Order-01 | `test_checkout_orders_api.py` | A |
| OBS-F-013 | Order total | `services/pricing.py` | TC-Order-02 | `tests/unit/test_pricing.py`, `test_checkout_orders_api.py` | A |
| OBS-F-014 | Payment request | `orders.py` `checkout`, `mock_gateway.py` | TC-Pay-01 | `test_checkout_orders_api.py` | A |
| OBS-F-015 | Paid only after valid success | `orders.py` `payment_result` | TC-Pay-02 | `test_checkout_orders_api.py` | A |
| OBS-F-016 | Unique order number | `orders.py` `payment_result` | TC-Order-03 | `test_checkout_orders_api.py` | A |
| OBS-F-017 | Stock reduced after confirmed order | `services/inventory.py` `deduct_stock` | TC-Inv-01, TC-Cart-04 | `test_inventory_service.py`, `test_checkout_orders_api.py` | A |
| OBS-F-018 | Order history / status | `orders.py` `my_orders` | TC-Order-04 | `test_checkout_orders_api.py` | A |
| OBS-F-019 | Cancel order | `orders.py` `cancel_order` | TC-Order-05 | `test_checkout_orders_api.py` | A |
| OBS-F-020 | Admin add book | `routers/admin.py` `add_book` | TC-Admin-01 | `test_admin_api.py` | A |
| OBS-F-021 | Admin edit/deactivate | `admin.py` `edit_book` | TC-Admin-02 | `test_admin_api.py` | A |
| OBS-F-022 | Categories | `admin.py` `add_category`, `rename_category` | TC-Admin-03 | `test_admin_api.py` | A |
| OBS-F-023 | Stock / reorder level | `admin.py` `update_inventory` | TC-Inv-02 | `test_inventory_service.py`, `test_admin_api.py` | A |
| OBS-F-024 | Low-stock identification | `inventory.py` `low_stock_books` | TC-Inv-03 | `test_inventory_service.py`, `test_admin_api.py` | A |
| OBS-F-025 | Admin order status | `admin.py` `update_order_status` | TC-Admin-04 | `test_admin_api.py` | A |
| OBS-F-026 | Sales + inventory reports | `admin.py` `sales_report`, `inventory_report` | TC-Rep-01 | `test_admin_api.py` | A |

## Non-functional requirements

| Req ID | Requirement | How verified | Test case | Status |
|---|---|---|---|---|
| OBS-NF-001 | p90 ≤ 3 s | `tests/integration/test_scale_performance.py` (40 requests, 20 threads, 10,000 books) | TC-Perf-01 | A |
| OBS-NF-002 | 99.5% availability | `GET /api/health` exists; needs 30-day measurement | TC-Reliability-01 | P |
| OBS-NF-003 | First-time usability | Manual user test (5 users) | TC-UX-01 | P |
| OBS-NF-004 | 10,000 books / 20 sessions | `test_scale_performance.py` | TC-Scale-01 | A |
| OBS-NF-005 | Desktop/tablet/mobile | Responsive CSS; manual check at 1200 px and 390 px | TC-UX-02 | P |
| OBS-NF-006 | Admin audit trail | `audit.py`, `GET /api/admin/audit-log`; `test_admin_api.py` | TC-Audit-01 | A |

## Security requirements

| Req ID | Requirement | How verified | Test case | Status |
|---|---|---|---|---|
| OBS-SR-001 | Authentication required | `security.get_current_user`; `test_auth_api.py`, `test_admin_api.py` | TC-Sec-01 | A |
| OBS-SR-002 | Salted password hashes | `passwords.py`; `tests/unit/test_passwords.py` | TC-Sec-02 | A |
| OBS-SR-003 | RBAC | `security.require_admin`; `test_admin_api.py` (customer → 403) | TC-Sec-03 | A |
| OBS-SR-004 | Secure communication | HTTPS at deployment (see DEVIATIONS C) | TC-Sec-04 | P |
| OBS-SR-005 | Input validation | pydantic validation + ORM parameters; injection tests in `test_auth_api.py`, `test_catalogue_api.py` | TC-Sec-05 | A |
| OBS-SR-006 | Verify payment response | `services/payment.py`; `test_payment_signature.py`, `test_checkout_orders_api.py` | TC-Sec-06 | A |
