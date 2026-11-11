# Online Bookstore System — Team 4

Software Engineering mini-project (PES University). A web-based bookstore where customers browse, search and buy books,
and administrators manage books, stock, orders and reports.

| Document | Version | Purpose |
|---|---|---|
| Software Requirements Specification (SRS) | 1.0 (09-09-2026) | 26 functional, 6 non-functional, 6 security requirements |
| Software Architecture & Design (SAD) | 1.0 (14-09-2026) | Layered REST architecture, API design, STRIDE security |
| Software Test Plan (STP) | 1.0 (16-09-2026) | Test strategy and test-case IDs |

**Status:** Sprint 1 and Sprint 2 complete; development frozen (v1.0). The sections below describe the final system.

Everything in this repo traces back to those three documents (see [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md)).
Where we differ from them, it is written down in [`docs/DEVIATIONS.md`](docs/DEVIATIONS.md).

## Team

| Member | SRN | Sprint 1 | Sprint 2 |
|---|---|---|---|
| Aanya K | PES2UG24CS011 | Authentication & Authorization (F-001–003, SR-001/002) | Inventory (F-017, 023, 024), load/scale tests (NF-001, NF-004), usability tests (NF-003, NF-005), test summary |
| Aaruni Choudhary (repo owner) | PES2UG24CS013 | Repo, CI/CD, backlog + Project board, Cart (F-009–011), input validation (SR-005) | Checkout, Order & Payment (F-012–016, 018, 019, SR-006) |
| Aditya R Badde | PES2UG25CS802 | Catalogue & Search (F-004–008), demo/test data | Administration (F-020–022, 025), Reporting (F-026), audit (NF-006), RBAC (SR-003), TLS note (SR-004), NF-002 |

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| UI | Plain HTML + CSS + JavaScript (responsive, no build step) | Works on desktop/tablet/mobile (NF-005) |
| API | Python 3 + FastAPI (REST, auto docs at `/docs`) | SAD 3.6: "REST APIs (e.g. Spring Boot **or an equivalent framework**)" |
| Data | SQLAlchemy ORM + SQLite | SAD 3.6: relational DB behind an ORM; parameterised queries (SR-005) |
| Tests | pytest + FastAPI TestClient, coverage via pytest-cov | STP levels: unit, integration, system |
| CI | GitHub Actions (`.github/workflows/ci.yml`) | Build + run all tests on every push / PR |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.seed               # demo books + accounts  (use --books 10000 for the full STP catalogue)
uvicorn app.main:app --reload        # open http://127.0.0.1:8000   (API docs: /docs)
```

Demo accounts (created by the seed script):

| Role | Email | Password |
|---|---|---|
| Administrator | admin@bookstore.local | Admin@1234 |
| Customer | customer@example.com | Customer@123 |

## Run the tests

```bash
pytest                                # all tests (~15 s)
pytest tests/unit                     # unit tests only
pytest tests/integration              # integration + system tests
pytest --cov=app --cov-report=term-missing   # with coverage
```

## Project layout

```
app/
  main.py            wires everything together, standard error format
  config.py database.py models.py security.py audit.py   shared foundation
  passwords.py       salted password hashing               (OBS-SR-002)
  routers/
    auth.py          register / login / logout             (OBS-F-001..003)
    catalogue.py     browse / search / filter / sort       (OBS-F-004..008)
    cart.py          cart                                  (OBS-F-009..011, 013)
    orders.py        checkout, payment callback, orders    (OBS-F-012, 014..016, 018, 019, SR-006)
    mock_gateway.py  simulated external payment service
    admin.py         books, categories, inventory, orders, reports, audit log
  services/
    inventory.py     stock deduct / restore / low-stock    (OBS-F-017, 023, 024)
    pricing.py       totals, delivery, discount            (OBS-F-013)
    payment.py       HMAC signing / verification           (OBS-SR-006)
  static/            the web UI (index.html, css/, js/)
tests/
  unit/              one module at a time
  integration/       API + database together, plus an end-to-end journey
scripts/             seed.py (demo data), create_issues.sh (backlog -> GitHub issues)
docs/                SRS/SAD/STP deviations, traceability matrix, backlog, test summary
.github/workflows/   CI pipeline
```

## Architecture in one paragraph

A layered monolith (SAD 3.5): the browser UI calls REST endpoints; each router is one SAD component
(Auth, Catalogue, Cart & Checkout, Order & Payment, Inventory, Reporting); services hold business rules;
SQLAlchemy persists to the database. Payments go through a mock gateway that signs its answers with
HMAC-SHA256; the server only marks an order **paid** after verifying that signature, and only then deducts stock.

## Branching and workflow

* `main` is protected: changes arrive through pull requests only; the repo owner reviews and merges.
* Branch names: `feature/<module>`, e.g. `feature/auth`. One backlog issue ↔ one or more commits ↔ one PR (`Closes #n`).
* CI must be green before a merge.
