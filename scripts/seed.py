"""Load demo / test data.

    python -m scripts.seed                 # 60 books + admin + demo customer
    python -m scripts.seed --books 10000   # the 10,000-record catalogue from the STP

Accounts created (only if they do not exist yet):
    admin@bookstore.local     / Admin@1234      (role: admin)
    customer@example.com      / Customer@123    (role: customer)
"""
import argparse
import os
import random

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Book, Cart, Category, User
from app.passwords import hash_password

CATEGORIES = ["Fiction", "Non-Fiction", "Science", "Technology", "History", "Children", "Self-Help"]

REAL_BOOKS = [
    ("Clean Code", "Robert C. Martin", "9780132350884", "Technology", 899.0),
    ("The Pragmatic Programmer", "Andrew Hunt", "9780135957059", "Technology", 1099.0),
    ("Introduction to Algorithms", "Thomas H. Cormen", "9780262046305", "Technology", 1799.0),
    ("A Brief History of Time", "Stephen Hawking", "9780553380163", "Science", 499.0),
    ("Sapiens", "Yuval Noah Harari", "9780062316097", "History", 599.0),
    ("Atomic Habits", "James Clear", "9780735211292", "Self-Help", 549.0),
    ("The Alchemist", "Paulo Coelho", "9780062315007", "Fiction", 299.0),
    ("Wings of Fire", "A. P. J. Abdul Kalam", "9788173711466", "Non-Fiction", 250.0),
]

ADJECTIVES = ["Silent", "Hidden", "Golden", "Broken", "Endless", "Crimson", "Forgotten", "Distant", "Brave", "Quiet"]
NOUNS = ["River", "Garden", "Empire", "Machine", "Letter", "Mountain", "Algorithm", "Voyage", "Secret", "Harvest"]
FIRST = ["Asha", "Ravi", "Meera", "John", "Priya", "Arjun", "Nina", "Karan", "Sara", "Dev"]
LAST = ["Sharma", "Iyer", "Nair", "Smith", "Rao", "Mehta", "Khan", "Das", "Patel", "Reddy"]


def seed_books(db: Session, count: int) -> int:
    """Insert `count` books in one bulk operation. Returns how many were added."""
    rng = random.Random(42)  # fixed seed: same data on every machine
    categories = {c.name: c for c in db.scalars(select(Category))}
    for name in CATEGORIES:
        if name not in categories:
            categories[name] = Category(name=name)
            db.add(categories[name])
    db.flush()

    existing = {isbn for (isbn,) in db.execute(select(Book.isbn))}
    rows = []
    for title, author, isbn, cat, price in REAL_BOOKS:
        if isbn not in existing and len(rows) < count:
            rows.append(Book(title=title, author=author, isbn=isbn, price=price, category_id=categories[cat].id,
                             description=f"{title} by {author}.", stock=rng.randint(3, 40), reorder_level=5))
    n = 0
    while len(rows) < count:
        n += 1
        isbn = f"979{n:010d}"
        if isbn in existing:
            continue
        title = f"The {rng.choice(ADJECTIVES)} {rng.choice(NOUNS)} {n}"
        rows.append(Book(
            title=title, author=f"{rng.choice(FIRST)} {rng.choice(LAST)}", isbn=isbn,
            price=float(rng.randint(99, 1999)), category_id=categories[rng.choice(CATEGORIES)].id,
            description=f"A sample book used for testing: {title}.", stock=rng.choice([0, 2, 5, 12, 25, 40]),
            reorder_level=5,
        ))
    db.add_all(rows)
    db.commit()
    return len(rows)


def ensure_user(db: Session, email: str, password: str, name: str, role: str) -> None:
    if db.scalar(select(User).where(User.email == email)):
        return
    user = User(email=email, password_hash=hash_password(password), full_name=name, role=role)
    db.add(user)
    db.flush()
    db.add(Cart(user_id=user.id))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--books", type=int, default=60)
    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Book)):
            added = 0
            print("Books already exist - skipping book seeding (delete bookstore.db to start fresh).")
        else:
            added = seed_books(db, args.books)
        admin_password = os.getenv("ADMIN_PASSWORD", "Admin@1234")
        ensure_user(db, "admin@bookstore.local", admin_password, "Store Admin", "admin")
        ensure_user(db, "customer@example.com", "Customer@123", "Demo Customer", "customer")
    print(f"Seeded {added} books. Admin account: admin@bookstore.local")


if __name__ == "__main__":
    main()
