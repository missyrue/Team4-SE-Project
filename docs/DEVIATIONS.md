# Deviations from the submitted SRS / SAD / STP

The sprint brief says deviations are allowed if documented and explained at the demo. Each one below has the
**reason** and the **effect**. Everything not listed here follows the documents.

## A. Technology choices (SAD 3.6 only gave examples)

| # | Document said | We built | Reason |
|---|---|---|---|
| A1 | Frontend "e.g. React" | Plain HTML/CSS/JS, one file per screen | SAD says *e.g.*; no build tooling, runs by opening the server URL; still responsive (OBS-NF-005) |
| A2 | Backend "e.g. Spring Boot **or an equivalent framework**" | Python FastAPI | Explicitly allowed by "equivalent framework"; fastest to build and test |
| A3 | "Relational database e.g. MySQL/PostgreSQL" | SQLite through SQLAlchemy ORM | Zero setup for the demo; the ORM means switching to MySQL/PostgreSQL only needs `DATABASE_URL` |
| A4 | STP tools: Selenium, Postman, JMeter, OWASP ZAP, Jira | pytest + FastAPI TestClient; GitHub Issues/Projects | Everything is automated in CI. Load test (TC-Perf-01, TC-Scale-01) is scripted in pytest with 20 threads and 10,000 books instead of JMeter |

## B. Design clarifications / conflicts between our own documents

| # | Issue found | Decision |
|---|---|---|
| B1 | SAD sequence diagram 3 shows **"reserve stock"** before payment; SRS OBS-F-017 and STP TC-Cart-04 say stock is reduced **only after confirmed payment** | We follow the SRS/STP: stock is *checked* at add-to-cart and checkout, *deducted* only when a verified successful payment arrives. No reservation, so nothing needs releasing on failure/timeout |
| B2 | Stock sold out between checkout and payment (two buyers, one copy) | The deduction is atomic (`UPDATE … WHERE stock >= qty`). The second order is **cancelled** with a clear message. A real refund is out of scope (gateway internals excluded by SRS 1.2) |
| B3 | SAD API shows checkout response with `orderNumber`; SRS OBS-F-016 says the number is created *after successful confirmation* | `orderNumber` is `null` at checkout and issued when payment is confirmed (format `OBS-YYYYMMDD-00012`) |
| B4 | SAD sequence diagram has *Cart & Checkout Service* creating the order, API table puts `/api/orders/checkout` under *Order & Payment Service* | Cart contents live in the cart router; `POST /api/orders/checkout` (order creation) lives in the orders router and reads the cart |
| B5 | SAD component diagram shows a "Customer Service" (profile, order history, cancel) not described in §3.4 | Its functions are covered by Auth (`/api/auth/me`) and Orders (`/api/orders…`) — no separate component |
| B6 | SRS says "delivery charges and applicable discounts" without values | Delivery ₹40, free from ₹500 subtotal; 10% discount from ₹2000 subtotal (`app/services/pricing.py`) |
| B7 | SAD API error table lists 400/409/401/404/204 | Implemented exactly: validation errors → 400, stock conflict → 409, bad signature → 401, no search match → 204 |
| B8 | SAD says "session-token" authentication | Random token stored in the DB (so logout truly ends the session); not JWT |
| B9 | Admin order status values were undefined (SRS "Status values required") | `pending_payment → paid → processing → shipped → delivered`, plus `payment_failed` and `cancelled`. Customer can cancel while pending/paid/processing |
| B10 | Payment gateway sandbox | A built-in **mock gateway** (`/api/mock-gateway/pay`) returns HMAC-signed success / failed / tampered results — STP risk table allows mocked responses |

## C. Not implemented (and why)

| Item | Document | Status |
|---|---|---|
| TLS in the application (OBS-SR-004, TC-Sec-04) | SRS 5.1.2 | Done at **deployment** (HTTPS reverse proxy / hosting platform), not in app code. Verified manually, not by an automated test |
| Rate limiting on login/search (SAD STRIDE "Denial of service") | SAD 3.9 | Not implemented. Search is paginated (max 100 per page) and indexed instead |
| Catalogue caching / CDN | SAD 3.7, 4.6 | Not needed: p90 stays far below 3 s with 10,000 books (TC-Perf-01) |
| Notification service | SRS 3.3 optional, STP §4 out of scope | Not built |
| 99.5% monthly availability (OBS-NF-002, TC-Reliability-01) | SRS 5 | Needs a 30-day measurement (STP says so too). We provide `GET /api/health` for monitoring |
| Usability studies (TC-UX-01/02) | SRS 5 | Manual: tested on desktop and a 390 px phone viewport; 4-of-5 first-time-user study is a manual activity |
| Penetration testing / fuzzing with OWASP ZAP | STP 5.1 | Not run. Injection and malformed-input cases are covered by automated tests (TC-Sec-05) |

## D. Documentation issues found in our own SRS/STP (to correct in the next document revision)

* SRS RTM writes test IDs like `TC-Order01`, `TC-Audit01`; STP and tests use `TC-Order-01`, `TC-Audit-01`.
* `TC-Cart-04` exists in the STP but not in the SRS RTM; OBS-F-017 is therefore covered by `TC-Inv-01` **and** `TC-Cart-04`.
* The RTM design-spec IDs `DS-Fxxx` are not defined anywhere in the SAD.
* SAD status is still "Draft"; STP roles table has no names; the ER diagram was an open issue (now `app/models.py`).
