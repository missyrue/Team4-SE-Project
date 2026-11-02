"""UNIT tests - Inventory Service (TC-Inv-01..03)."""
import pytest

from app.services import inventory


def test_TC_Inv_01_deduct_stock_reduces_quantity(db, make_book):
    book = make_book(stock=10)
    inventory.deduct_stock(db, [(book.id, 3)])
    db.commit()
    db.refresh(book)
    assert book.stock == 7


def test_TC_Inv_01_deduct_exactly_all_stock_is_allowed(db, make_book):
    book = make_book(stock=3)
    inventory.deduct_stock(db, [(book.id, 3)])  # boundary: qty == stock
    db.commit()
    db.refresh(book)
    assert book.stock == 0


def test_TC_Inv_01_deduct_more_than_stock_raises_and_changes_nothing(db, make_book):
    book = make_book(stock=3)
    with pytest.raises(inventory.InsufficientStock):
        inventory.deduct_stock(db, [(book.id, 4)])  # boundary: stock + 1
    db.refresh(book)
    assert book.stock == 3


def test_TC_Inv_01_multi_item_deduction_is_all_or_nothing(db, make_book):
    plenty, scarce = make_book(title="Plenty", stock=10), make_book(title="Scarce", stock=1)
    with pytest.raises(inventory.InsufficientStock) as err:
        inventory.deduct_stock(db, [(plenty.id, 2), (scarce.id, 5)])
    assert err.value.book_id == scarce.id
    db.refresh(plenty)
    db.refresh(scarce)
    assert (plenty.stock, scarce.stock) == (10, 1)  # the first line was rolled back too


@pytest.mark.parametrize("quantity", [0, -1])
def test_deduct_stock_rejects_non_positive_quantity_without_changing_stock(db, make_book, quantity):
    book = make_book(stock=10)
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        inventory.deduct_stock(db, [(book.id, quantity)])
    db.refresh(book)
    assert book.stock == 10


def test_deduct_stock_validates_all_quantities_before_updating(db, make_book):
    first, second = make_book(title="First", stock=10), make_book(title="Second", stock=10)
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        inventory.deduct_stock(db, [(first.id, 2), (second.id, 0)])
    db.refresh(first)
    db.refresh(second)
    assert (first.stock, second.stock) == (10, 10)


def test_restore_stock_adds_quantity_back(db, make_book):
    book = make_book(stock=5)
    inventory.restore_stock(db, [(book.id, 2)])
    db.commit()
    db.refresh(book)
    assert book.stock == 7


@pytest.mark.parametrize("quantity", [0, -1])
def test_restore_stock_rejects_non_positive_quantity_without_changing_stock(db, make_book, quantity):
    book = make_book(stock=5)
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        inventory.restore_stock(db, [(book.id, quantity)])
    db.refresh(book)
    assert book.stock == 5


def test_restore_stock_rejects_missing_book_before_updating_other_books(db, make_book):
    book = make_book(stock=5)
    with pytest.raises(ValueError, match="book 99999 does not exist"):
        inventory.restore_stock(db, [(book.id, 2), (99999, 1)])
    db.refresh(book)
    assert book.stock == 5


def test_TC_Inv_02_update_stock_and_reorder_level(db, make_book):
    book = make_book(stock=5, reorder_level=5)
    inventory.update_stock(db, book, stock=40, reorder_level=10)
    db.commit()
    assert (book.stock, book.reorder_level) == (40, 10)


def test_TC_Inv_02_update_stock_can_change_only_one_field(db, make_book):
    book = make_book(stock=5, reorder_level=5)
    inventory.update_stock(db, book, stock=9)
    assert (book.stock, book.reorder_level) == (9, 5)


def test_TC_Inv_02_negative_values_are_rejected(db, make_book):
    book = make_book()
    with pytest.raises(ValueError):
        inventory.update_stock(db, book, stock=-1)
    with pytest.raises(ValueError):
        inventory.update_stock(db, book, reorder_level=-1)


def test_TC_Inv_02_invalid_reorder_level_does_not_partially_update_stock(db, make_book):
    book = make_book(stock=5, reorder_level=3)
    with pytest.raises(ValueError, match="reorder level cannot be negative"):
        inventory.update_stock(db, book, stock=20, reorder_level=-1)
    db.refresh(book)
    assert (book.stock, book.reorder_level) == (5, 3)


def test_get_stock_level(db, make_book):
    book = make_book(stock=12)
    assert inventory.get_stock_level(db, book.id) == 12
    assert inventory.get_stock_level(db, 99999) == 0


@pytest.mark.parametrize("stock, expected", [(6, False), (5, True), (4, True), (0, True)])
def test_TC_Inv_03_needs_reorder_boundary_at_reorder_level(make_book, stock, expected):
    assert inventory.needs_reorder(make_book(stock=stock, reorder_level=5)) is expected  # AT the level counts


def test_TC_Inv_03_low_stock_books_lists_only_books_at_or_below_level(db, make_book):
    make_book(title="Fine", stock=6, reorder_level=5)
    make_book(title="AtLevel", stock=5, reorder_level=5)
    make_book(title="Empty", stock=0, reorder_level=5)
    make_book(title="Inactive", stock=0, reorder_level=5, is_active=False)  # deactivated books are ignored
    assert [b.title for b in inventory.low_stock_books(db)] == ["Empty", "AtLevel"]
