"""UNIT tests - catalogue helper functions (OBS-F-005, OBS-SR-005)."""
from app.routers.catalogue import SORT_ORDER, book_to_dict, escape_like


def test_escape_like_makes_wildcards_literal():
    assert escape_like("100%") == "100\\%"
    assert escape_like("a_b") == "a\\_b"
    assert escape_like("plain") == "plain"


def test_all_four_sort_options_exist():
    assert set(SORT_ORDER) == {"title_asc", "title_desc", "price_asc", "price_desc"}


def test_book_to_dict_availability_in_stock(make_book):
    book = make_book(stock=3)
    assert book_to_dict(book)["availability"] == "In stock"


def test_book_to_dict_availability_boundary_zero_stock(make_book):
    book = make_book(stock=0)  # boundary: exactly zero
    assert book_to_dict(book)["availability"] == "Out of stock"


def test_book_to_dict_detail_includes_description(make_book):
    book = make_book(title="Dune")
    assert "description" not in book_to_dict(book)
    assert book_to_dict(book, detail=True)["description"] == "About Dune"
