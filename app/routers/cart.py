"""Cart & Checkout Service - cart part (SAD 3.4)

OBS-F-009  POST   /api/cart/items          add a book + quantity
OBS-F-010  PUT    /api/cart/items/{bookId} change quantity
           DELETE /api/cart/items/{bookId} remove an item
OBS-F-011  quantity above available stock is rejected (409)
OBS-F-013  GET    /api/cart                subtotal / discount / delivery / total preview
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, Cart, CartItem, User
from app.security import get_current_user
from app.services.pricing import calculate_totals

router = APIRouter(prefix="/api/cart", tags=["cart"])


class AddItemIn(BaseModel):
    bookId: int
    quantity: int = Field(ge=1, le=100)


class UpdateItemIn(BaseModel):
    quantity: int = Field(ge=1, le=100)


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
    return cart


def serialize_cart(cart: Cart) -> dict:
    items = []
    subtotal = 0.0
    for item in cart.items:
        line_total = round(item.book.price * item.quantity, 2)
        subtotal += line_total
        items.append(
            {
                "bookId": item.book_id,
                "title": item.book.title,
                "unitPrice": item.book.price,
                "quantity": item.quantity,
                "lineTotal": line_total,
                "stock": item.book.stock,
            }
        )
    return {"cartId": cart.id, "items": items, **calculate_totals(subtotal)}


def _check_stock(book: Book, wanted: int) -> None:
    if book.stock <= 0:
        raise HTTPException(status_code=409, detail=f"'{book.title}' is out of stock")
    if wanted > book.stock:
        raise HTTPException(status_code=409, detail=f"Only {book.stock} copies of '{book.title}' are available")


def _active_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None or not book.is_active:
        raise HTTPException(status_code=404, detail="Book not found or no longer available")
    return book


@router.get("")
def view_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return serialize_cart(get_or_create_cart(db, user))


@router.post("/items", status_code=201)
def add_item(body: AddItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = _active_book(db, body.bookId)
    cart = get_or_create_cart(db, user)
    existing = next((i for i in cart.items if i.book_id == book.id), None)
    new_quantity = body.quantity + (existing.quantity if existing else 0)
    _check_stock(book, new_quantity)
    if existing:
        existing.quantity = new_quantity
    else:
        db.add(CartItem(cart_id=cart.id, book_id=book.id, quantity=body.quantity))
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@router.put("/items/{book_id}")
def update_item(book_id: int, body: UpdateItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, user)
    item = next((i for i in cart.items if i.book_id == book_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item is not in your cart")
    _check_stock(item.book, body.quantity)
    item.quantity = body.quantity
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@router.delete("/items/{book_id}")
def remove_item(book_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, user)
    item = next((i for i in cart.items if i.book_id == book_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item is not in your cart")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)
