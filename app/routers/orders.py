"""Order & Payment Service (SAD 3.4)

OBS-F-012  POST /api/orders/checkout                 delivery details + create order
OBS-F-013  totals via app/services/pricing.py
OBS-F-014  checkout returns a paymentRequestId for the gateway
OBS-F-015  POST /api/orders/{id}/payment-result      ONLY a valid signed "success" marks paid
OBS-F-016  unique order number on confirmation
OBS-F-017  stock is deducted only here, after confirmed payment
OBS-F-018  GET  /api/orders, /api/orders/{id}        customer sees only their own orders
OBS-F-019  POST /api/orders/{id}/cancel
OBS-SR-006 payment result signature is verified (HMAC) before anything changes
"""
import re
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CUSTOMER_CANCELLABLE, STOCK_DEDUCTED_STATES, Cart, Order, OrderItem, User, utcnow
from app.security import get_current_user
from app.services import inventory, payment
from app.services.pricing import calculate_totals

router = APIRouter(prefix="/api/orders", tags=["orders"])

PHONE_RE = re.compile(r"^\+?[0-9]{10,13}$")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class CheckoutIn(BaseModel):
    cartId: int
    deliveryAddress: str = Field(min_length=10, max_length=300)
    contactDetails: str = Field(min_length=10, max_length=30)

    @field_validator("deliveryAddress")
    @classmethod
    def clean_address(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10 or CONTROL_CHARS.search(v):
            raise ValueError("must be at least 10 characters and contain no control characters")
        return v

    @field_validator("contactDetails")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        compact = re.sub(r"[\s-]", "", v)
        if not PHONE_RE.match(compact):
            raise ValueError("must be a valid phone number (10-13 digits)")
        return compact


class PaymentResultIn(BaseModel):
    paymentRequestId: str
    result: Literal["success", "failed"]
    signature: str


def serialize_order(order: Order) -> dict:
    return {
        "orderId": order.id,
        "orderNumber": order.order_number,
        "status": order.status,
        "subtotal": order.subtotal,
        "discount": order.discount,
        "deliveryCharge": order.delivery_charge,
        "total": order.total,
        "deliveryAddress": order.delivery_address,
        "contactDetails": order.contact_details,
        "createdAt": order.created_at.isoformat(),
        "items": [
            {"bookId": i.book_id, "title": i.title, "unitPrice": i.unit_price, "quantity": i.quantity}
            for i in order.items
        ],
    }


def _order_items(order: Order) -> list[tuple[int, int]]:
    return [(i.book_id, i.quantity) for i in order.items]


@router.post("/checkout", status_code=201)
def checkout(body: CheckoutIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.get(Cart, body.cartId)
    if cart is None or cart.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cart not found")
    if not cart.items:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    subtotal = 0.0
    for item in cart.items:
        book = item.book
        if not book.is_active:
            raise HTTPException(status_code=409, detail=f"'{book.title}' is no longer available")
        if item.quantity > book.stock:  # stock is only CHECKED here, never reduced (OBS-F-017)
            raise HTTPException(status_code=409, detail=f"Only {book.stock} copies of '{book.title}' are available")
        subtotal += book.price * item.quantity

    totals = calculate_totals(subtotal)
    order = Order(
        user_id=user.id,
        status="pending_payment",
        subtotal=totals["subtotal"],
        discount=totals["discount"],
        delivery_charge=totals["deliveryCharge"],
        total=totals["total"],
        delivery_address=body.deliveryAddress,
        contact_details=body.contactDetails,
        payment_request_id=uuid.uuid4().hex,
    )
    order.items = [
        OrderItem(book_id=i.book_id, title=i.book.title, unit_price=i.book.price, quantity=i.quantity)
        for i in cart.items
    ]
    db.add(order)
    db.commit()
    return {
        "orderId": order.id,
        "orderNumber": order.order_number,  # null until payment is confirmed (SRS OBS-F-016)
        "status": order.status,
        "total": order.total,
        "paymentRequestId": order.payment_request_id,
    }


@router.post("/{order_id}/payment-result")
def payment_result(order_id: int, body: PaymentResultIn, db: Session = Depends(get_db)):
    """Callback from the payment gateway. No login: the HMAC signature proves who sent it."""
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Unknown order")
    if body.paymentRequestId != order.payment_request_id or not payment.verify(
        body.paymentRequestId, body.result, body.signature
    ):
        # Forged / altered result: change NOTHING (OBS-SR-006).
        raise HTTPException(status_code=401, detail="Invalid payment signature")

    if order.status != "pending_payment":
        if order.status in ("paid", "processing", "shipped", "delivered") and body.result == "success":
            return {"orderId": order.id, "status": order.status, "orderNumber": order.order_number}  # idempotent replay
        raise HTTPException(status_code=409, detail="This order is not awaiting payment")

    if body.result == "failed":
        order.status = "payment_failed"  # stock untouched (TC-Cart-04)
        db.commit()
        return {"orderId": order.id, "status": order.status, "orderNumber": None}

    try:
        inventory.deduct_stock(db, _order_items(order))  # all-or-nothing
    except inventory.InsufficientStock:
        order = db.get(Order, order_id)
        order.status = "cancelled"
        db.commit()
        raise HTTPException(status_code=409, detail="Stock ran out before payment was confirmed; the order was cancelled")

    order.status = "paid"
    order.paid_at = utcnow()
    order.order_number = f"OBS-{order.paid_at:%Y%m%d}-{order.id:05d}"  # unique because id is unique (OBS-F-016)
    cart = db.scalar(select(Cart).where(Cart.user_id == order.user_id))
    if cart:
        cart.items.clear()  # purchased: empty the cart
    db.commit()
    return {"orderId": order.id, "status": order.status, "orderNumber": order.order_number}


@router.get("")
def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc()))
    return [serialize_order(o) for o in orders]


@router.get("/{order_id}")
def my_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:  # other people's orders look like "not found"
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize_order(order)


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in CUSTOMER_CANCELLABLE:
        raise HTTPException(status_code=409, detail=f"An order that is '{order.status}' can no longer be cancelled")
    if order.status in STOCK_DEDUCTED_STATES:
        inventory.restore_stock(db, _order_items(order))  # give the stock back
    order.status = "cancelled"
    db.commit()
    return serialize_order(order)
