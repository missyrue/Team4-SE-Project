"""INTEGRATION tests - Checkout, Payment, Orders (Order & Payment Service + Inventory + DB).

TC-Order-01..05, TC-Pay-01..02, TC-Cart-04, TC-Inv-01, TC-Sec-06
"""
import pytest

from app.models import Book, Order

ADDRESS = "12 MG Road, Bengaluru 560001"
PHONE = "9876543210"


def _fill_cart(client, headers, book, quantity=1):
    return client.post("/api/cart/items", json={"bookId": book.id, "quantity": quantity}, headers=headers).json()


def _checkout(client, headers, cart_id, address=ADDRESS, phone=PHONE):
    return client.post(
        "/api/orders/checkout",
        json={"cartId": cart_id, "deliveryAddress": address, "contactDetails": phone},
        headers=headers,
    )


def _gateway(client, order_json, outcome):
    """Ask the mock gateway for a signed result for this order's payment request."""
    return client.post("/api/mock-gateway/pay", json={"paymentRequestId": order_json["paymentRequestId"], "outcome": outcome}).json()


def _pay(client, order_json, outcome="success"):
    payload = _gateway(client, order_json, outcome)
    return client.post(f"/api/orders/{order_json['orderId']}/payment-result", json=payload)


@pytest.fixture()
def placed(client, customer_header, make_book):
    """A customer who has checked out 2 copies of a Rs 300 book (stock 10), payment still pending."""
    book = make_book(title="Dune", price=300, stock=10)
    cart = _fill_cart(client, customer_header, book, 2)
    order = _checkout(client, customer_header, cart["cartId"]).json()
    return book, order


# ------------------------------------------------------------------ TC-Order-01
def test_TC_Order_01_checkout_with_valid_details_creates_pending_order(client, customer_header, make_book):
    cart = _fill_cart(client, customer_header, make_book(price=300), 1)
    r = _checkout(client, customer_header, cart["cartId"])
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending_payment"
    assert body["orderNumber"] is None          # number is only issued after payment is confirmed
    assert body["paymentRequestId"]


@pytest.mark.parametrize(
    "address, phone",
    [
        ("", PHONE),                       # missing address
        ("short", PHONE),                  # boundary: 5 chars (<10)
        (ADDRESS, ""),                     # missing phone
        (ADDRESS, "12345"),                # phone too short
        (ADDRESS, "98765abcde"),           # letters in phone
    ],
)
def test_TC_Order_01_checkout_rejects_missing_or_invalid_details(client, customer_header, make_book, address, phone):
    cart = _fill_cart(client, customer_header, make_book(), 1)
    assert _checkout(client, customer_header, cart["cartId"], address, phone).status_code == 400


def test_TC_Order_01_address_exactly_10_characters_is_accepted(client, customer_header, make_book):
    cart = _fill_cart(client, customer_header, make_book(), 1)
    assert _checkout(client, customer_header, cart["cartId"], address="1234567890").status_code == 201


def test_TC_Order_01_empty_cart_cannot_checkout(client, customer_header, customer):
    cart = client.get("/api/cart", headers=customer_header).json()
    assert _checkout(client, customer_header, cart["cartId"]).status_code == 400


def test_checkout_of_someone_elses_cart_is_404(client, make_user, auth_header, make_book):
    alice, bob = auth_header(make_user("alice@t.com")), auth_header(make_user("bob@t.com"))
    alice_cart = _fill_cart(client, alice, make_book(), 1)
    assert _checkout(client, bob, alice_cart["cartId"]).status_code == 404


def test_checkout_requires_login(client):
    r = client.post("/api/orders/checkout", json={"cartId": 1, "deliveryAddress": ADDRESS, "contactDetails": PHONE})
    assert r.status_code == 401


# ------------------------------------------------------------------ TC-Order-02
def test_TC_Order_02_order_total_matches_displayed_cart_total(client, customer_header, make_book):
    book = make_book(price=250, stock=20)
    cart = _fill_cart(client, customer_header, book, 1)   # 250 -> +40 delivery = 290
    assert cart["total"] == 290
    order = _checkout(client, customer_header, cart["cartId"]).json()
    assert order["total"] == cart["total"] == 290


def test_TC_Order_02_total_with_free_delivery_and_discount(client, customer_header, make_book):
    book = make_book(price=1000, stock=20)
    cart = _fill_cart(client, customer_header, book, 2)   # 2000 - 10% = 1800, free delivery
    order = _checkout(client, customer_header, cart["cartId"]).json()
    assert order["total"] == 1800


# ------------------------------------------------------------------ TC-Pay-01
def test_TC_Pay_01_payment_request_has_order_amount_and_gateway_returns_signed_result(client, placed):
    _, order = placed
    assert order["total"] == 600                       # 2 x 300 = 600, free delivery (>= 500)
    signed = _gateway(client, order, "success")
    assert signed["paymentRequestId"] == order["paymentRequestId"]
    assert signed["result"] == "success" and signed["signature"]


# ------------------------------------------------------------------ TC-Pay-02
def test_TC_Pay_02_successful_signed_result_marks_order_paid(client, placed, customer_header):
    _, order = placed
    r = _pay(client, order, "success")
    assert r.status_code == 200
    assert r.json()["status"] == "paid"
    assert client.get(f"/api/orders/{order['orderId']}", headers=customer_header).json()["status"] == "paid"


def test_TC_Pay_02_failed_result_does_not_mark_order_paid(client, placed, customer_header):
    _, order = placed
    r = _pay(client, order, "failed")
    assert r.status_code == 200
    assert r.json()["status"] == "payment_failed"
    assert client.get(f"/api/orders/{order['orderId']}", headers=customer_header).json()["status"] == "payment_failed"


# ------------------------------------------------------------------ TC-Order-03
def test_TC_Order_03_each_confirmed_order_gets_a_unique_order_number(client, customer_header, make_book):
    book = make_book(price=300, stock=50)
    numbers = []
    for _ in range(3):
        cart = _fill_cart(client, customer_header, book, 1)
        order = _checkout(client, customer_header, cart["cartId"]).json()
        numbers.append(_pay(client, order).json()["orderNumber"])
    assert all(n and n.startswith("OBS-") for n in numbers)
    assert len(set(numbers)) == 3


def test_TC_Order_03_no_order_number_before_payment_is_confirmed(client, placed, customer_header):
    _, order = placed
    assert client.get(f"/api/orders/{order['orderId']}", headers=customer_header).json()["orderNumber"] is None


# ------------------------------------------------------------------ TC-Cart-04 / TC-Inv-01
def test_TC_Cart_04_failed_payment_does_not_reduce_stock(client, placed, db):
    book, order = placed
    _pay(client, order, "failed")
    db.refresh(book)
    assert book.stock == 10


def test_TC_Cart_04_stock_untouched_while_payment_is_pending(client, placed, db):
    book, _ = placed          # checkout done, payment never completed
    db.refresh(book)
    assert book.stock == 10


def test_TC_Inv_01_confirmed_payment_reduces_stock_by_ordered_quantity(client, placed, db):
    book, order = placed
    _pay(client, order, "success")
    db.refresh(book)
    assert book.stock == 8    # 10 - 2


def test_cart_is_emptied_after_successful_payment(client, placed, customer_header):
    _, order = placed
    _pay(client, order, "success")
    assert client.get("/api/cart", headers=customer_header).json()["items"] == []


def test_cart_is_kept_after_failed_payment_so_customer_can_retry(client, placed, customer_header):
    _, order = placed
    _pay(client, order, "failed")
    assert len(client.get("/api/cart", headers=customer_header).json()["items"]) == 1


def test_last_copy_cannot_be_sold_twice(client, make_user, auth_header, make_book, db):
    book = make_book(stock=1, price=300)
    alice, bob = auth_header(make_user("alice@t.com")), auth_header(make_user("bob@t.com"))
    order_a = _checkout(client, alice, _fill_cart(client, alice, book, 1)["cartId"]).json()
    order_b = _checkout(client, bob, _fill_cart(client, bob, book, 1)["cartId"]).json()
    assert _pay(client, order_a).status_code == 200
    second = _pay(client, order_b)
    assert second.status_code == 409                     # stock ran out before Bob's payment came back
    db.refresh(book)
    assert book.stock == 0                               # never negative
    assert client.get(f"/api/orders/{order_b['orderId']}", headers=bob).json()["status"] == "cancelled"


# ------------------------------------------------------------------ TC-Order-04
def test_TC_Order_04_customer_sees_only_their_own_orders(client, make_user, auth_header, make_book):
    book = make_book(price=300, stock=20)
    alice, bob = auth_header(make_user("alice@t.com")), auth_header(make_user("bob@t.com"))
    order_a = _checkout(client, alice, _fill_cart(client, alice, book, 1)["cartId"]).json()
    _pay(client, order_a)
    mine = client.get("/api/orders", headers=alice).json()
    assert [o["orderId"] for o in mine] == [order_a["orderId"]]
    assert mine[0]["status"] == "paid" and mine[0]["items"][0]["title"] == book.title
    assert client.get("/api/orders", headers=bob).json() == []
    assert client.get(f"/api/orders/{order_a['orderId']}", headers=bob).status_code == 404  # cannot peek


# ------------------------------------------------------------------ TC-Order-05
def test_TC_Order_05_cancel_pending_order(client, placed, customer_header):
    _, order = placed
    r = client.post(f"/api/orders/{order['orderId']}/cancel", headers=customer_header)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"


def test_TC_Order_05_cancel_paid_order_gives_stock_back(client, placed, customer_header, db):
    book, order = placed
    _pay(client, order, "success")
    db.refresh(book)
    assert book.stock == 8
    assert client.post(f"/api/orders/{order['orderId']}/cancel", headers=customer_header).status_code == 200
    db.refresh(book)
    assert book.stock == 10


@pytest.mark.parametrize("status", ["shipped", "delivered", "cancelled", "payment_failed"])
def test_TC_Order_05_non_cancellable_order_is_rejected_with_message(client, placed, customer_header, db, status):
    _, order = placed
    db.get(Order, order["orderId"]).status = status
    db.commit()
    r = client.post(f"/api/orders/{order['orderId']}/cancel", headers=customer_header)
    assert r.status_code == 409
    assert "can no longer be cancelled" in r.json()["message"]


def test_cannot_cancel_someone_elses_order(client, placed, make_user, auth_header):
    _, order = placed
    other = auth_header(make_user("other@t.com"))
    assert client.post(f"/api/orders/{order['orderId']}/cancel", headers=other).status_code == 404


# ------------------------------------------------------------------ TC-Sec-06
def test_TC_Sec_06_tampered_payment_result_is_rejected_and_order_not_paid(client, placed, customer_header, db):
    book, order = placed
    r = _pay(client, order, "tampered")        # says "success" but the signature is for "failed"
    assert r.status_code == 401
    assert client.get(f"/api/orders/{order['orderId']}", headers=customer_header).json()["status"] == "pending_payment"
    db.refresh(book)
    assert book.stock == 10


def test_TC_Sec_06_payment_for_a_different_request_id_is_rejected(client, placed):
    _, order = placed
    forged = {"paymentRequestId": "other-id", "result": "success", "signature": "0" * 64}
    assert client.post(f"/api/orders/{order['orderId']}/payment-result", json=forged).status_code == 401


def test_TC_Sec_06_missing_gateway_response_leaves_order_unpaid(client, placed, customer_header):
    """Communication failure / timeout: no callback ever arrives -> never 'paid'."""
    _, order = placed
    assert client.get(f"/api/orders/{order['orderId']}", headers=customer_header).json()["status"] == "pending_payment"


def test_TC_Sec_06_unknown_order_is_404(client):
    body = {"paymentRequestId": "x", "result": "success", "signature": "y"}
    assert client.post("/api/orders/9999/payment-result", json=body).status_code == 404


def test_replayed_success_result_is_idempotent_and_deducts_stock_once(client, placed, db):
    book, order = placed
    signed = _gateway(client, order, "success")
    url = f"/api/orders/{order['orderId']}/payment-result"
    assert client.post(url, json=signed).status_code == 200
    assert client.post(url, json=signed).status_code == 200      # same callback delivered twice
    db.refresh(book)
    assert book.stock == 8                                       # still only 2 removed


def test_failed_order_cannot_be_flipped_to_paid_later(client, placed):
    _, order = placed
    _pay(client, order, "failed")
    assert _pay(client, order, "success").status_code == 409
