"""INTEGRATION tests - Administrator API (TC-Admin-01..04, TC-Inv-02/03, TC-Rep-01, TC-Audit-01, TC-Sec-01/03)."""
from datetime import datetime, timedelta

import pytest

from app.models import Order, OrderItem, utcnow


def _category(client, admin_header, name="Fiction"):
    return client.post("/api/admin/categories", json={"name": name}, headers=admin_header).json()


def _new_book(client, admin_header, category_id, **overrides):
    body = {"title": "New Book", "author": "A. Writer", "isbn": "9781234567897", "price": 350,
            "categoryId": category_id, "stock": 10, "reorderLevel": 5, **overrides}
    return client.post("/api/admin/books", json=body, headers=admin_header)


# ------------------------------------------------------------------ security
ADMIN_ENDPOINTS = [
    ("get", "/api/admin/books"),
    ("get", "/api/admin/orders"),
    ("get", "/api/admin/inventory/low-stock"),
    ("get", "/api/admin/reports/inventory"),
    ("get", "/api/admin/audit-log"),
]


@pytest.mark.parametrize("method, url", ADMIN_ENDPOINTS)
def test_TC_Sec_01_admin_endpoints_need_login(client, method, url):
    assert getattr(client, method)(url).status_code == 401


@pytest.mark.parametrize("method, url", ADMIN_ENDPOINTS)
def test_TC_Sec_03_customer_cannot_use_admin_endpoints(client, customer_header, method, url):
    assert getattr(client, method)(url, headers=customer_header).status_code == 403


def test_TC_Sec_03_customer_cannot_create_books_or_change_orders(client, customer_header):
    assert client.post("/api/admin/books", json={}, headers=customer_header).status_code == 403
    assert client.put("/api/admin/orders/1/status", json={"status": "shipped"}, headers=customer_header).status_code == 403


# ------------------------------------------------------------------ TC-Admin-01
def test_TC_Admin_01_add_book_appears_in_public_catalogue(client, admin_header):
    cat = _category(client, admin_header)
    r = _new_book(client, admin_header, cat["id"], title="Brand New")
    assert r.status_code == 201
    titles = [b["title"] for b in client.get("/api/books").json()["results"]]
    assert titles == ["Brand New"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": ""},                 # missing title
        {"price": 0},                  # boundary: must be > 0
        {"price": -5},
        {"stock": -1},
        {"isbn": "abc"},               # bad ISBN
        {"categoryId": 9999},          # unknown category
    ],
)
def test_TC_Admin_01_invalid_book_data_is_rejected(client, admin_header, overrides):
    cat = _category(client, admin_header)
    overrides = dict(overrides)
    category_id = overrides.pop("categoryId", cat["id"])
    assert _new_book(client, admin_header, category_id, **overrides).status_code == 400


def test_TC_Admin_01_duplicate_isbn_is_rejected(client, admin_header):
    cat = _category(client, admin_header)
    assert _new_book(client, admin_header, cat["id"]).status_code == 201
    assert _new_book(client, admin_header, cat["id"], title="Another").status_code == 409


# ------------------------------------------------------------------ TC-Admin-02
def test_TC_Admin_02_edit_book_saves_changes(client, admin_header):
    cat = _category(client, admin_header)
    book = _new_book(client, admin_header, cat["id"]).json()
    r = client.put(f"/api/admin/books/{book['id']}", json={"title": "Renamed", "price": 499}, headers=admin_header)
    assert r.status_code == 200
    detail = client.get(f"/api/books/{book['id']}").json()
    assert detail["title"] == "Renamed" and detail["price"] == 499


def test_TC_Admin_02_deactivated_book_is_hidden_and_cannot_be_bought(client, admin_header, customer_header):
    cat = _category(client, admin_header)
    book = _new_book(client, admin_header, cat["id"]).json()
    client.put(f"/api/admin/books/{book['id']}", json={"isActive": False}, headers=admin_header)
    assert client.get("/api/books").json()["count"] == 0
    assert client.get(f"/api/books/{book['id']}").status_code == 404
    r = client.post("/api/cart/items", json={"bookId": book["id"], "quantity": 1}, headers=customer_header)
    assert r.status_code == 404


def test_TC_Admin_02_unknown_book_is_404(client, admin_header):
    assert client.put("/api/admin/books/9999", json={"title": "x"}, headers=admin_header).status_code == 404


# ------------------------------------------------------------------ TC-Admin-03
def test_TC_Admin_03_create_and_rename_category_reflected_in_filtering(client, admin_header):
    cat = _category(client, admin_header, "Sci-Fi")
    _new_book(client, admin_header, cat["id"], title="Space Book")
    assert client.put(f"/api/admin/categories/{cat['id']}", json={"name": "Science Fiction"}, headers=admin_header).status_code == 200
    r = client.get("/api/books/search", params={"category": "Science Fiction"})
    assert [b["title"] for b in r.json()["results"]] == ["Space Book"]
    assert client.get("/api/books/search", params={"category": "Sci-Fi"}).status_code == 204  # old name gone


def test_TC_Admin_03_duplicate_or_blank_category_is_rejected(client, admin_header):
    _category(client, admin_header, "Poetry")
    assert client.post("/api/admin/categories", json={"name": "Poetry"}, headers=admin_header).status_code == 409
    assert client.post("/api/admin/categories", json={"name": "   "}, headers=admin_header).status_code == 400


# ------------------------------------------------------------------ TC-Inv-02 / TC-Inv-03
def test_TC_Inv_02_update_stock_is_reflected_in_availability(client, admin_header):
    cat = _category(client, admin_header)
    book = _new_book(client, admin_header, cat["id"], stock=0).json()
    assert client.get(f"/api/books/{book['id']}").json()["availability"] == "Out of stock"
    r = client.put(f"/api/admin/inventory/{book['id']}", json={"stock": 25, "reorderLevel": 8}, headers=admin_header)
    assert r.status_code == 200
    assert r.json()["stock"] == 25 and r.json()["reorderLevel"] == 8
    assert client.get(f"/api/books/{book['id']}").json()["availability"] == "In stock"


def test_TC_Inv_02_negative_stock_or_empty_update_is_rejected(client, admin_header):
    cat = _category(client, admin_header)
    book = _new_book(client, admin_header, cat["id"]).json()
    assert client.put(f"/api/admin/inventory/{book['id']}", json={"stock": -1}, headers=admin_header).status_code == 400
    assert client.put(f"/api/admin/inventory/{book['id']}", json={}, headers=admin_header).status_code == 400


def test_TC_Inv_03_update_response_flags_low_stock_immediately(client, admin_header):
    cat = _category(client, admin_header)
    book = _new_book(client, admin_header, cat["id"], stock=50, reorderLevel=5).json()
    assert book["lowStock"] is False
    r = client.put(f"/api/admin/inventory/{book['id']}", json={"stock": 5}, headers=admin_header)  # exactly at the level
    assert r.json()["lowStock"] is True


def test_TC_Inv_03_low_stock_list_contains_only_books_at_or_below_level(client, admin_header, make_book):
    make_book(title="Fine", stock=20, reorder_level=5)
    make_book(title="AtLevel", stock=5, reorder_level=5)
    make_book(title="Below", stock=1, reorder_level=5)
    r = client.get("/api/admin/inventory/low-stock", headers=admin_header)
    assert r.json()["count"] == 2
    assert [b["title"] for b in r.json()["books"]] == ["Below", "AtLevel"]


# ------------------------------------------------------------------ TC-Admin-04
def _paid_order(db, user, book, qty=1, status="paid", paid_at=None):
    order = Order(user_id=user.id, status=status, subtotal=book.price * qty, total=book.price * qty,
                  delivery_address="12 MG Road, Bengaluru", contact_details="9876543210",
                  payment_request_id=f"req-{book.id}-{status}-{datetime.now().timestamp()}", paid_at=paid_at or utcnow())
    order.items = [OrderItem(book_id=book.id, title=book.title, unit_price=book.price, quantity=qty)]
    db.add(order)
    db.commit()
    return order


def test_TC_Admin_04_status_update_is_visible_to_the_customer(client, admin_header, customer, customer_header, make_book, db):
    order = _paid_order(db, customer, make_book(price=300))
    assert client.put(f"/api/admin/orders/{order.id}/status", json={"status": "processing"}, headers=admin_header).status_code == 200
    assert client.put(f"/api/admin/orders/{order.id}/status", json={"status": "shipped"}, headers=admin_header).status_code == 200
    assert client.get(f"/api/orders/{order.id}", headers=customer_header).json()["status"] == "shipped"


def test_TC_Admin_04_invalid_status_change_is_rejected(client, admin_header, customer, make_book, db):
    order = _paid_order(db, customer, make_book(), status="paid")
    assert client.put(f"/api/admin/orders/{order.id}/status", json={"status": "delivered"}, headers=admin_header).status_code == 409  # cannot skip steps
    assert client.put(f"/api/admin/orders/{order.id}/status", json={"status": "paid"}, headers=admin_header).status_code == 400          # not an allowed target
    assert client.put("/api/admin/orders/9999/status", json={"status": "shipped"}, headers=admin_header).status_code == 404


def test_TC_Admin_04_admin_cancel_restores_stock(client, admin_header, customer, make_book, db):
    book = make_book(stock=10)
    order = _paid_order(db, customer, book, qty=2)  # (stock was already reduced when it was paid)
    book.stock = 8
    db.commit()
    client.put(f"/api/admin/orders/{order.id}/status", json={"status": "cancelled"}, headers=admin_header)
    db.refresh(book)
    assert book.stock == 10


def test_admin_can_list_and_filter_all_orders(client, admin_header, customer, make_book, db):
    book = make_book()
    _paid_order(db, customer, book, status="paid")
    _paid_order(db, customer, book, status="shipped")
    assert len(client.get("/api/admin/orders", headers=admin_header).json()) == 2
    assert len(client.get("/api/admin/orders", params={"status": "shipped"}, headers=admin_header).json()) == 1


# ------------------------------------------------------------------ TC-Rep-01
def test_TC_Rep_01_sales_report_totals_match_stored_orders(client, admin_header, customer, make_book, db):
    a, b = make_book(title="A", price=100), make_book(title="B", price=200)
    _paid_order(db, customer, a, qty=2)           # 200
    _paid_order(db, customer, b, qty=1)           # 200
    _paid_order(db, customer, a, qty=1, status="payment_failed")   # failed payments are NOT sales
    today = utcnow().date().isoformat()
    r = client.get("/api/admin/reports/sales", params={"start": today, "end": today}, headers=admin_header)
    assert r.status_code == 200
    body = r.json()
    assert body["orders"] == 2 and body["revenue"] == 400 and body["itemsSold"] == 3
    assert body["topBooks"][0] == {"title": "A", "quantity": 2}


def test_TC_Rep_01_period_filter_excludes_orders_outside_the_period(client, admin_header, customer, make_book, db):
    book = make_book()
    _paid_order(db, customer, book, paid_at=utcnow() - timedelta(days=10))
    today = utcnow().date()
    r = client.get("/api/admin/reports/sales", params={"start": (today - timedelta(days=2)).isoformat(), "end": today.isoformat()}, headers=admin_header)
    assert r.json()["orders"] == 0


def test_TC_Rep_01_end_date_is_inclusive(client, admin_header, customer, make_book, db):
    book = make_book()
    late = utcnow().replace(hour=23, minute=59, second=59)
    _paid_order(db, customer, book, paid_at=late)
    today = utcnow().date().isoformat()
    assert client.get("/api/admin/reports/sales", params={"start": today, "end": today}, headers=admin_header).json()["orders"] == 1


def test_TC_Rep_01_start_after_end_or_bad_date_is_rejected(client, admin_header):
    assert client.get("/api/admin/reports/sales", params={"start": "2026-10-10", "end": "2026-10-01"}, headers=admin_header).status_code == 400
    assert client.get("/api/admin/reports/sales", params={"start": "yesterday", "end": "today"}, headers=admin_header).status_code == 400


def test_TC_Rep_01_inventory_report_counts_match(client, admin_header, make_book):
    make_book(stock=20)
    make_book(stock=5, reorder_level=5)
    make_book(stock=0)
    body = client.get("/api/admin/reports/inventory", headers=admin_header).json()
    assert body["totalBooks"] == 3 and body["totalUnits"] == 25
    assert body["outOfStock"] == 1 and body["lowStockCount"] == 2


# ------------------------------------------------------------------ TC-Audit-01
def test_TC_Audit_01_every_admin_change_is_recorded_with_user_action_record_and_time(client, admin_header):
    cat = _category(client, admin_header, "Audit Cat")
    book = _new_book(client, admin_header, cat["id"]).json()
    client.put(f"/api/admin/books/{book['id']}", json={"price": 999}, headers=admin_header)
    client.put(f"/api/admin/inventory/{book['id']}", json={"stock": 3}, headers=admin_header)
    log = client.get("/api/admin/audit-log", headers=admin_header).json()
    assert [row["action"] for row in log] == ["inventory.update", "book.update", "book.create", "category.create"]
    newest = log[0]
    assert newest["record"] == f"book:{book['id']}" and newest["userId"] and newest["time"]
    assert "stock=3" in newest["detail"]


def test_TC_Audit_01_failed_changes_are_not_logged(client, admin_header):
    client.post("/api/admin/books", json={"title": ""}, headers=admin_header)
    assert client.get("/api/admin/audit-log", headers=admin_header).json() == []
