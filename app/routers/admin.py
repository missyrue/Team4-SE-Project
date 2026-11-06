"""Administrator functions (SAD: Admin UI + Catalogue/Inventory/Reporting services)

Every endpoint here needs an admin session (OBS-SR-001 / OBS-SR-003):
no token -> 401, customer token -> 403.

OBS-F-020  POST /api/admin/books                       add a book
OBS-F-021  PUT  /api/admin/books/{id}                  edit / deactivate (isActive=false)
OBS-F-022  POST /api/admin/categories, PUT .../{id}    create / rename categories
OBS-F-023  PUT  /api/admin/inventory/{bookId}          stock + reorder level
OBS-F-024  GET  /api/admin/inventory/low-stock         stock <= reorder level
OBS-F-025  GET  /api/admin/orders, PUT .../orders/{id}/status
OBS-F-026  GET  /api/admin/reports/sales?start=&end=, /reports/inventory
OBS-NF-006 GET  /api/admin/audit-log   (every change above writes an audit row)
"""
import re
from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit import log_action
from app.database import get_db
from app.models import PAID_STATES, STOCK_DEDUCTED_STATES, AuditLog, Book, Category, Order, User
from app.routers.catalogue import book_to_dict
from app.security import require_admin
from app.services import inventory

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])

ISBN_RE = re.compile(r"^[0-9Xx-]{10,17}$")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _text(value: str) -> str:
    value = value.strip()
    if not value or CONTROL_CHARS.search(value):
        raise ValueError("must not be empty or contain control characters")
    return value


# ----------------------------------------------------------------- schemas
class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    isbn: str
    description: str = Field(default="", max_length=2000)
    price: float = Field(gt=0, le=100000)
    categoryId: int
    stock: int = Field(default=0, ge=0, le=1_000_000)
    reorderLevel: int = Field(default=5, ge=0, le=1_000_000)
    isActive: bool = True

    @field_validator("title", "author")
    @classmethod
    def clean(cls, v):
        return _text(v)

    @field_validator("isbn")
    @classmethod
    def valid_isbn(cls, v):
        v = v.strip()
        if not ISBN_RE.match(v):
            raise ValueError("must be 10-17 characters: digits, X or hyphens")
        return v


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    price: float | None = Field(default=None, gt=0, le=100000)
    categoryId: int | None = None
    isActive: bool | None = None

    @field_validator("title", "author")
    @classmethod
    def clean(cls, v):
        return _text(v) if v is not None else v


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def clean(cls, v):
        return _text(v)


class InventoryIn(BaseModel):
    stock: int | None = Field(default=None, ge=0, le=1_000_000)
    reorderLevel: int | None = Field(default=None, ge=0, le=1_000_000)


class StatusIn(BaseModel):
    status: Literal["processing", "shipped", "delivered", "cancelled"]


# Allowed order-status changes made by an administrator.
TRANSITIONS = {
    "pending_payment": {"cancelled"},
    "paid": {"processing", "cancelled"},
    "processing": {"shipped", "cancelled"},
    "shipped": {"delivered"},
}


def _admin_book(db: Session, book_id: int) -> Book:
    book = db.scalar(select(Book).options(joinedload(Book.category)).where(Book.id == book_id))
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


def _require_category(db: Session, category_id: int) -> None:
    if db.get(Category, category_id) is None:
        raise HTTPException(status_code=400, detail="Unknown category")


def _admin_book_dict(book: Book) -> dict:
    data = book_to_dict(book, detail=True)
    data.update({"reorderLevel": book.reorder_level, "isActive": book.is_active, "lowStock": inventory.needs_reorder(book)})
    return data


# ------------------------------------------------------------------- books
@router.get("/books")
def admin_list_books(q: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Book).options(joinedload(Book.category)).order_by(Book.title).limit(200)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(Book.title.ilike(like) | Book.isbn.ilike(like))
    return [_admin_book_dict(b) for b in db.scalars(stmt).unique()]


@router.post("/books", status_code=201)
def add_book(body: BookIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    _require_category(db, body.categoryId)
    if db.scalar(select(Book).where(Book.isbn == body.isbn)):
        raise HTTPException(status_code=409, detail="A book with this ISBN already exists")
    book = Book(
        title=body.title, author=body.author, isbn=body.isbn, description=body.description,
        price=body.price, category_id=body.categoryId, stock=body.stock,
        reorder_level=body.reorderLevel, is_active=body.isActive,
    )
    db.add(book)
    db.flush()
    log_action(db, admin.id, "book.create", f"book:{book.id}", f"title={book.title}")
    db.commit()
    return _admin_book_dict(_admin_book(db, book.id))


@router.put("/books/{book_id}")
def edit_book(book_id: int, body: BookUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    book = _admin_book(db, book_id)
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if "categoryId" in changes:
        _require_category(db, changes["categoryId"])
    field_map = {"categoryId": "category_id", "isActive": "is_active"}
    for key, value in changes.items():
        setattr(book, field_map.get(key, key), value)
    log_action(db, admin.id, "book.update", f"book:{book.id}", ", ".join(f"{k}={v}" for k, v in changes.items()))
    db.commit()
    return _admin_book_dict(_admin_book(db, book_id))


# -------------------------------------------------------------- categories
@router.post("/categories", status_code=201)
def add_category(body: CategoryIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    category = Category(name=body.name)
    db.add(category)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category already exists")
    log_action(db, admin.id, "category.create", f"category:{category.id}", f"name={category.name}")
    db.commit()
    return {"id": category.id, "name": category.name}


@router.put("/categories/{category_id}")
def rename_category(category_id: int, body: CategoryIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    old = category.name
    category.name = body.name
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category already exists")
    log_action(db, admin.id, "category.update", f"category:{category.id}", f"{old} -> {body.name}")
    db.commit()
    return {"id": category.id, "name": category.name}


# --------------------------------------------------------------- inventory
@router.put("/inventory/{book_id}")
def update_inventory(book_id: int, body: InventoryIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if body.stock is None and body.reorderLevel is None:
        raise HTTPException(status_code=400, detail="Provide stock and/or reorderLevel")
    book = _admin_book(db, book_id)
    inventory.update_stock(db, book, stock=body.stock, reorder_level=body.reorderLevel)
    log_action(db, admin.id, "inventory.update", f"book:{book.id}", f"stock={book.stock}, reorderLevel={book.reorder_level}")
    db.commit()
    return _admin_book_dict(book)  # includes lowStock flag so the UI can warn immediately


@router.get("/inventory/low-stock")
def low_stock(db: Session = Depends(get_db)):
    books = inventory.low_stock_books(db)
    return {"count": len(books), "books": [_admin_book_dict(b) for b in books]}


# ------------------------------------------------------------------ orders
def _admin_order_dict(order: Order) -> dict:
    return {
        "orderId": order.id,
        "orderNumber": order.order_number,
        "customerId": order.user_id,
        "status": order.status,
        "total": order.total,
        "createdAt": order.created_at.isoformat(),
        "items": [{"title": i.title, "quantity": i.quantity} for i in order.items],
    }


@router.get("/orders")
def admin_orders(status: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Order).order_by(Order.id.desc()).limit(200)
    if status:
        stmt = stmt.where(Order.status == status)
    return [_admin_order_dict(o) for o in db.scalars(stmt)]


@router.put("/orders/{order_id}/status")
def update_order_status(order_id: int, body: StatusIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if body.status not in TRANSITIONS.get(order.status, set()):
        raise HTTPException(status_code=409, detail=f"Cannot change an order from '{order.status}' to '{body.status}'")
    if body.status == "cancelled" and order.status in STOCK_DEDUCTED_STATES:
        inventory.restore_stock(db, [(i.book_id, i.quantity) for i in order.items])
    previous = order.status
    order.status = body.status
    log_action(db, admin.id, "order.status", f"order:{order.id}", f"{previous} -> {body.status}")
    db.commit()
    return _admin_order_dict(order)


# ----------------------------------------------------------------- reports
@router.get("/reports/sales")
def sales_report(start: date, end: date, db: Session = Depends(get_db)):
    if start > end:
        raise HTTPException(status_code=400, detail="start must not be after end")
    begin = datetime.combine(start, time.min)
    finish = datetime.combine(end + timedelta(days=1), time.min)  # end date is inclusive
    orders = db.scalars(
        select(Order).where(Order.status.in_(PAID_STATES), Order.paid_at >= begin, Order.paid_at < finish)
    ).all()
    per_book: dict[str, int] = {}
    for order in orders:
        for item in order.items:
            per_book[item.title] = per_book.get(item.title, 0) + item.quantity
    top = sorted(per_book.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "orders": len(orders),
        "revenue": round(sum(o.total for o in orders), 2),
        "itemsSold": sum(per_book.values()),
        "topBooks": [{"title": t, "quantity": q} for t, q in top],
    }


@router.get("/reports/inventory")
def inventory_report(db: Session = Depends(get_db)):
    total_books = db.scalar(select(func.count()).select_from(Book)) or 0
    total_units = db.scalar(select(func.coalesce(func.sum(Book.stock), 0))) or 0
    out_of_stock = db.scalar(select(func.count()).select_from(Book).where(Book.stock == 0)) or 0
    low = inventory.low_stock_books(db)
    return {
        "totalBooks": total_books,
        "totalUnits": int(total_units),
        "outOfStock": out_of_stock,
        "lowStockCount": len(low),
        "lowStock": [{"id": b.id, "title": b.title, "stock": b.stock, "reorderLevel": b.reorder_level} for b in low[:50]],
    }


# --------------------------------------------------------------- audit log
@router.get("/audit-log")
def audit_log(limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit))
    return [
        {"id": r.id, "userId": r.user_id, "action": r.action, "record": r.record, "detail": r.detail, "time": r.created_at.isoformat()}
        for r in rows
    ]
