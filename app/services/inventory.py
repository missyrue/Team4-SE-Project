"""Inventory Service (SAD 3.4): stock levels, reorder checks, deduct / restore.

OBS-F-017  deduct_stock  - only called after a payment is confirmed
OBS-F-023  update_stock  - admin changes stock / reorder level
OBS-F-024  low_stock_books - books at or below their reorder level
"""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Book


class InsufficientStock(Exception):
    def __init__(self, book_id: int):
        super().__init__(f"Insufficient stock for book {book_id}")
        self.book_id = book_id


def get_stock_level(db: Session, book_id: int) -> int:
    book = db.get(Book, book_id)
    return book.stock if book else 0


def needs_reorder(book: Book) -> bool:
    """True when stock is AT or BELOW the reorder level (boundary included)."""
    return book.stock <= book.reorder_level


def low_stock_books(db: Session) -> list[Book]:
    stmt = (
        select(Book)
        .where(Book.is_active.is_(True), Book.stock <= Book.reorder_level)
        .order_by(Book.stock.asc(), Book.title.asc())
    )
    return list(db.scalars(stmt))


def deduct_stock(db: Session, items: list[tuple[int, int]]) -> None:
    """Remove stock for [(book_id, qty), ...] as ONE all-or-nothing operation.

    Each UPDATE only succeeds while stock >= qty, so two buyers can never push
    stock below zero (SAD risk: concurrent purchases oversell). If any line
    cannot be satisfied the whole transaction is rolled back and
    InsufficientStock is raised, so stock is never half-deducted.
    """
    items = list(items)
    for _, qty in items:
        if qty <= 0:
            raise ValueError("quantity must be greater than zero")

    for book_id, qty in items:
        result = db.execute(
            update(Book).where(Book.id == book_id, Book.stock >= qty).values(stock=Book.stock - qty)
        )
        if result.rowcount != 1:
            db.rollback()
            raise InsufficientStock(book_id)
    db.flush()


def restore_stock(db: Session, items: list[tuple[int, int]]) -> None:
    """Give stock back (order cancelled after it was deducted). Caller commits."""
    items = list(items)
    for _, qty in items:
        if qty <= 0:
            raise ValueError("quantity must be greater than zero")

    book_ids = {book_id for book_id, _ in items}
    if book_ids:
        existing_ids = set(db.scalars(select(Book.id).where(Book.id.in_(book_ids))))
        missing_ids = book_ids - existing_ids
        if missing_ids:
            missing_id = min(missing_ids)
            raise ValueError(f"book {missing_id} does not exist")

    for book_id, qty in items:
        result = db.execute(update(Book).where(Book.id == book_id).values(stock=Book.stock + qty))
        if result.rowcount != 1:
            db.rollback()
            raise ValueError(f"book {book_id} does not exist")
    db.flush()


def update_stock(db: Session, book: Book, stock: int | None = None, reorder_level: int | None = None) -> Book:
    """Admin update of stock quantity and/or reorder level. Caller commits."""
    if stock is not None and stock < 0:
        raise ValueError("stock cannot be negative")
    if reorder_level is not None and reorder_level < 0:
        raise ValueError("reorder level cannot be negative")

    if stock is not None:
        book.stock = stock
    if reorder_level is not None:
        book.reorder_level = reorder_level
    db.flush()
    return book
