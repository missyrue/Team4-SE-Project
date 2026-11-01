"""Catalogue Service (SAD 3.4)

OBS-F-004  GET /api/books                 active books with title/author/price/category/availability
OBS-F-005  GET /api/books/search?q=       search by title, author or ISBN
OBS-F-006  ...&category=&minPrice=&maxPrice=   filter
OBS-F-007  ...&sort=title_asc|title_desc|price_asc|price_desc
OBS-F-008  GET /api/books/{id}            full detail
(OBS-F-022 categories are maintained by the admin router; read-only list here)
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Book, Category

router = APIRouter(prefix="/api", tags=["catalogue"])

SORT_ORDER = {
    "title_asc": Book.title.asc(),
    "title_desc": Book.title.desc(),
    "price_asc": Book.price.asc(),
    "price_desc": Book.price.desc(),
}


def escape_like(text: str) -> str:
    """Make % and _ literal so users cannot craft wildcard-only searches."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def book_to_dict(book: Book, detail: bool = False) -> dict:
    data = {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "price": book.price,
        "category": book.category.name if book.category else None,
        "availability": "In stock" if book.stock > 0 else "Out of stock",
        "stock": book.stock,
    }
    if detail:
        data["description"] = book.description
    return data


def run_search(db: Session, q, category, min_price, max_price, sort, limit, offset) -> dict:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="minPrice cannot be greater than maxPrice")

    conditions = [Book.is_active.is_(True)]
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        conditions.append(
            Book.title.ilike(pattern, escape="\\")
            | Book.author.ilike(pattern, escape="\\")
            | Book.isbn.ilike(pattern, escape="\\")
        )
    if category:
        conditions.append(Book.category_id.in_(select(Category.id).where(func.lower(Category.name) == category.strip().lower())))
    if min_price is not None:
        conditions.append(Book.price >= min_price)
    if max_price is not None:
        conditions.append(Book.price <= max_price)

    total = db.scalar(select(func.count()).select_from(Book).where(*conditions)) or 0
    stmt = (
        select(Book)
        .options(joinedload(Book.category))
        .where(*conditions)
        .order_by(SORT_ORDER[sort], Book.id.asc())  # id = stable tie-breaker
        .limit(limit)
        .offset(offset)
    )
    books = db.scalars(stmt).unique().all()
    return {"results": [book_to_dict(b) for b in books], "count": total}


Sort = Literal["title_asc", "title_desc", "price_asc", "price_desc"]


@router.get("/books")
def list_books(
    sort: Sort = "title_asc",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return run_search(db, None, None, None, None, sort, limit, offset)


@router.get("/books/search")
def search_books(
    q: str | None = Query(None, max_length=100),
    category: str | None = Query(None, max_length=60),
    minPrice: float | None = Query(None, ge=0),
    maxPrice: float | None = Query(None, ge=0),
    sort: Sort = "title_asc",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    result = run_search(db, q, category, minPrice, maxPrice, sort, limit, offset)
    if result["count"] == 0:
        return Response(status_code=204)  # SAD 4.3: 204 when no books match
    return result


@router.get("/books/{book_id}")
def book_detail(book_id: int, db: Session = Depends(get_db)):
    book = db.scalar(select(Book).options(joinedload(Book.category)).where(Book.id == book_id, Book.is_active.is_(True)))
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_to_dict(book, detail=True)


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name} for c in db.scalars(select(Category).order_by(Category.name))]
