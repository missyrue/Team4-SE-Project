"""INTEGRATION tests - Cart API + catalogue + database (TC-Cart-01..03)."""


def _add(client, headers, book, quantity=1):
    return client.post("/api/cart/items", json={"bookId": book.id, "quantity": quantity}, headers=headers)


# ------------------------------------------------------------------ TC-Cart-01
def test_TC_Cart_01_add_book_shows_item_and_correct_subtotal(client, customer_header, make_book):
    book = make_book(title="Dune", price=250, stock=10)
    r = _add(client, customer_header, book, quantity=2)
    assert r.status_code == 201
    body = r.json()
    assert body["items"][0]["title"] == "Dune"
    assert body["items"][0]["quantity"] == 2
    assert body["items"][0]["lineTotal"] == 500
    assert body["subtotal"] == 500


def test_TC_Cart_01_adding_same_book_again_increases_quantity(client, customer_header, make_book):
    book = make_book(stock=10)
    _add(client, customer_header, book, 2)
    r = _add(client, customer_header, book, 3)
    assert r.json()["items"][0]["quantity"] == 5


def test_TC_Cart_01_unknown_or_inactive_book_is_404(client, customer_header, make_book):
    hidden = make_book(is_active=False)
    assert client.post("/api/cart/items", json={"bookId": 9999, "quantity": 1}, headers=customer_header).status_code == 404
    assert _add(client, customer_header, hidden).status_code == 404


def test_TC_Cart_01_quantity_zero_or_negative_is_rejected(client, customer_header, make_book):
    book = make_book()
    assert _add(client, customer_header, book, 0).status_code == 400
    assert _add(client, customer_header, book, -2).status_code == 400


def test_cart_requires_login(client, make_book):
    book = make_book()
    assert client.get("/api/cart").status_code == 401
    assert client.post("/api/cart/items", json={"bookId": book.id, "quantity": 1}).status_code == 401


# ------------------------------------------------------------------ TC-Cart-02
def test_TC_Cart_02_change_quantity_recalculates_total(client, customer_header, make_book):
    book = make_book(price=100, stock=10)
    _add(client, customer_header, book, 1)
    r = client.put(f"/api/cart/items/{book.id}", json={"quantity": 4}, headers=customer_header)
    assert r.status_code == 200
    assert r.json()["subtotal"] == 400


def test_TC_Cart_02_remove_item(client, customer_header, make_book):
    a, b = make_book(title="A", price=100), make_book(title="B", price=50)
    _add(client, customer_header, a)
    _add(client, customer_header, b)
    r = client.delete(f"/api/cart/items/{a.id}", headers=customer_header)
    assert [i["title"] for i in r.json()["items"]] == ["B"]
    assert r.json()["subtotal"] == 50


def test_TC_Cart_02_remove_item_not_in_cart_is_404(client, customer_header, make_book):
    book = make_book()
    assert client.delete(f"/api/cart/items/{book.id}", headers=customer_header).status_code == 404


def test_cart_preview_includes_delivery_and_discount(client, customer_header, make_book):
    book = make_book(price=2000, stock=5)
    body = _add(client, customer_header, book).json()
    assert body["discount"] == 200 and body["deliveryCharge"] == 0 and body["total"] == 1800


def test_each_customer_has_their_own_cart(client, make_user, auth_header, make_book):
    book = make_book(stock=10)
    a = auth_header(make_user("a@test.com"))
    b = auth_header(make_user("b@test.com"))
    _add(client, a, book, 3)
    assert client.get("/api/cart", headers=b).json()["items"] == []


# ------------------------------------------------------------------ TC-Cart-03
def test_TC_Cart_03_quantity_above_stock_is_rejected_with_message(client, customer_header, make_book):
    book = make_book(title="Dune", stock=3)
    r = _add(client, customer_header, book, 4)  # boundary: stock + 1
    assert r.status_code == 409
    assert "Only 3 copies" in r.json()["message"]


def test_TC_Cart_03_quantity_equal_to_stock_is_allowed(client, customer_header, make_book):
    book = make_book(stock=3)
    assert _add(client, customer_header, book, 3).status_code == 201  # boundary: exactly stock


def test_TC_Cart_03_cumulative_quantity_cannot_exceed_stock(client, customer_header, make_book):
    book = make_book(stock=3)
    _add(client, customer_header, book, 2)
    assert _add(client, customer_header, book, 2).status_code == 409  # 2 + 2 > 3


def test_TC_Cart_03_out_of_stock_book_cannot_be_added(client, customer_header, make_book):
    book = make_book(stock=0)
    r = _add(client, customer_header, book)
    assert r.status_code == 409 and "out of stock" in r.json()["message"]


def test_TC_Cart_03_updating_quantity_above_stock_is_rejected(client, customer_header, make_book):
    book = make_book(stock=3)
    _add(client, customer_header, book, 1)
    assert client.put(f"/api/cart/items/{book.id}", json={"quantity": 4}, headers=customer_header).status_code == 409
