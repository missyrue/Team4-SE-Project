"""SYSTEM test - the whole customer journey through every module (STP section 5, "System tests").

register -> login -> search -> add to cart -> checkout -> pay -> admin ships it -> report -> logout
"""
from app.models import User
from app.passwords import hash_password


def test_full_purchase_journey(client, db, make_book):
    # an administrator account (admins are created by the seed script, never via public signup)
    db.add(User(email="boss@store.com", password_hash=hash_password("Admin@1234"), full_name="Boss", role="admin"))
    db.commit()
    make_book(title="Clean Code", author="Robert Martin", price=900, stock=5, category="Technology")

    # 1. customer registers and logs in
    assert client.post("/api/auth/register", json={"email": "ravi@example.com", "password": "Passw0rd1", "fullName": "Ravi"}).status_code == 201
    token = client.post("/api/auth/login", json={"email": "ravi@example.com", "password": "Passw0rd1"}).json()["token"]
    me = {"Authorization": f"Bearer {token}"}

    # 2. searches the catalogue and opens the book
    found = client.get("/api/books/search", params={"q": "clean", "category": "Technology"}).json()["results"]
    assert len(found) == 1
    book_id = found[0]["id"]
    assert client.get(f"/api/books/{book_id}").json()["title"] == "Clean Code"

    # 3. adds 2 copies to the cart, checks the total
    cart = client.post("/api/cart/items", json={"bookId": book_id, "quantity": 2}, headers=me).json()
    assert cart["total"] == 1800  # 2 x 900, free delivery, no discount (<2000)

    # 4. checks out, pays through the mock gateway
    order = client.post("/api/orders/checkout", json={"cartId": cart["cartId"], "deliveryAddress": "12 MG Road, Bengaluru", "contactDetails": "9876543210"}, headers=me).json()
    signed = client.post("/api/mock-gateway/pay", json={"paymentRequestId": order["paymentRequestId"], "outcome": "success"}).json()
    paid = client.post(f"/api/orders/{order['orderId']}/payment-result", json=signed).json()
    assert paid["status"] == "paid" and paid["orderNumber"].startswith("OBS-")

    # 5. stock was reduced only now
    assert client.get(f"/api/books/{book_id}").json()["stock"] == 3

    # 6. administrator logs in, ships the order, checks reports
    admin_token = client.post("/api/auth/login", json={"email": "boss@store.com", "password": "Admin@1234"}).json()["token"]
    admin = {"Authorization": f"Bearer {admin_token}"}
    assert client.put(f"/api/admin/orders/{order['orderId']}/status", json={"status": "processing"}, headers=admin).status_code == 200
    assert client.put(f"/api/admin/orders/{order['orderId']}/status", json={"status": "shipped"}, headers=admin).status_code == 200
    assert client.get(f"/api/orders/{order['orderId']}", headers=me).json()["status"] == "shipped"  # customer sees it

    from datetime import date
    today = date.today().isoformat()
    sales = client.get("/api/admin/reports/sales", params={"start": today, "end": today}, headers=admin).json()
    assert sales["orders"] == 1 and sales["revenue"] == 1800 and sales["itemsSold"] == 2
    assert [row["action"] for row in client.get("/api/admin/audit-log", headers=admin).json()] == ["order.status", "order.status"]

    # 7. customer cannot reach admin data; logout ends the session
    assert client.get("/api/admin/orders", headers=me).status_code == 403
    assert client.post("/api/auth/logout", headers=me).status_code == 204
    assert client.get("/api/orders", headers=me).status_code == 401


def test_failed_payment_journey_keeps_stock_and_allows_retry(client, make_book, customer, customer_header, db):
    book = make_book(price=600, stock=4)
    cart = client.post("/api/cart/items", json={"bookId": book.id, "quantity": 1}, headers=customer_header).json()
    body = {"cartId": cart["cartId"], "deliveryAddress": "12 MG Road, Bengaluru", "contactDetails": "9876543210"}

    first = client.post("/api/orders/checkout", json=body, headers=customer_header).json()
    failed = client.post("/api/mock-gateway/pay", json={"paymentRequestId": first["paymentRequestId"], "outcome": "failed"}).json()
    assert client.post(f"/api/orders/{first['orderId']}/payment-result", json=failed).json()["status"] == "payment_failed"
    db.refresh(book)
    assert book.stock == 4                                         # nothing deducted

    second = client.post("/api/orders/checkout", json=body, headers=customer_header).json()   # cart still there -> retry
    good = client.post("/api/mock-gateway/pay", json={"paymentRequestId": second["paymentRequestId"], "outcome": "success"}).json()
    assert client.post(f"/api/orders/{second['orderId']}/payment-result", json=good).json()["status"] == "paid"
    db.refresh(book)
    assert book.stock == 3
