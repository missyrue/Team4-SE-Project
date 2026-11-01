"""Shared test fixtures. Every test gets a brand-new empty SQLite database file,
so tests never affect each other and never touch your real bookstore.db.

Fixtures
    db            SQLAlchemy session on the temporary database
    client        FastAPI TestClient wired to that database
    make_user     create a user directly (no login call needed) -> User
    auth_header   {"Authorization": "Bearer <token>"} for a user
    admin_header / customer_header   ready-made headers
    make_book     create a book quickly -> Book
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Book, Cart, Category, User
from app.security import create_session


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)  # not used as a context manager: skips the real-DB startup hook
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    def _make(email="user@example.com", role="customer", name="Test User"):
        user = User(email=email, password_hash="x", full_name=name, role=role)
        db.add(user)
        db.flush()
        db.add(Cart(user_id=user.id))
        db.commit()
        return user

    return _make


@pytest.fixture()
def auth_header(db):
    def _header(user):
        return {"Authorization": f"Bearer {create_session(db, user)}"}

    return _header


@pytest.fixture()
def admin_header(make_user, auth_header):
    return auth_header(make_user("admin@test.com", role="admin", name="Admin"))


@pytest.fixture()
def customer(make_user):
    return make_user("cust@test.com", role="customer", name="Customer")


@pytest.fixture()
def customer_header(customer, auth_header):
    return auth_header(customer)


@pytest.fixture()
def make_book(db):
    counter = {"n": 0}

    def _make(title="Test Book", author="Some Author", price=100.0, stock=10, category="Fiction",
              reorder_level=5, is_active=True, isbn=None):
        counter["n"] += 1
        cat = db.query(Category).filter_by(name=category).first()
        if cat is None:
            cat = Category(name=category)
            db.add(cat)
            db.flush()
        book = Book(title=title, author=author, isbn=isbn or f"978000000{counter['n']:04d}", price=price,
                    category_id=cat.id, stock=stock, reorder_level=reorder_level, is_active=is_active,
                    description=f"About {title}")
        db.add(book)
        db.commit()
        return book

    return _make
