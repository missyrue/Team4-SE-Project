"""INTEGRATION tests - Catalogue API + database (TC-Cat-01..04, TC-Book-01, TC-Sec-05)."""


def _titles(response):
    return [b["title"] for b in response.json()["results"]]


# ------------------------------------------------------------------ TC-Cat-01
def test_TC_Cat_01_lists_active_books_with_required_fields(client, make_book):
    make_book(title="Dune", author="Frank Herbert", price=399, category="Fiction", stock=4)
    make_book(title="Hidden Book", is_active=False)
    r = client.get("/api/books")
    assert r.status_code == 200
    assert _titles(r) == ["Dune"]  # inactive book is not shown
    book = r.json()["results"][0]
    for key in ("title", "author", "price", "category", "availability"):
        assert key in book
    assert book["availability"] == "In stock"


def test_TC_Cat_01_out_of_stock_book_shows_availability(client, make_book):
    make_book(title="Gone", stock=0)
    assert client.get("/api/books").json()["results"][0]["availability"] == "Out of stock"


# ------------------------------------------------------------------ TC-Cat-02
def test_TC_Cat_02_search_by_title_author_and_isbn(client, make_book):
    make_book(title="Clean Code", author="Robert Martin", isbn="9780132350884")
    make_book(title="Sapiens", author="Yuval Harari", isbn="9780062316097")
    assert _titles(client.get("/api/books/search", params={"q": "clean"})) == ["Clean Code"]
    assert _titles(client.get("/api/books/search", params={"q": "harari"})) == ["Sapiens"]
    assert _titles(client.get("/api/books/search", params={"q": "9780062316097"})) == ["Sapiens"]


def test_TC_Cat_02_no_match_returns_204_no_content(client, make_book):
    make_book(title="Dune")
    assert client.get("/api/books/search", params={"q": "zzzzzz"}).status_code == 204


def test_TC_Cat_02_percent_is_not_a_wildcard(client, make_book):
    make_book(title="Dune")
    assert client.get("/api/books/search", params={"q": "%"}).status_code == 204


# ------------------------------------------------------------------ TC-Cat-03
def test_TC_Cat_03_filter_by_category(client, make_book):
    make_book(title="A", category="Fiction")
    make_book(title="B", category="Science")
    r = client.get("/api/books/search", params={"category": "science"})
    assert _titles(r) == ["B"]


def test_TC_Cat_03_filter_by_price_range_boundaries_are_inclusive(client, make_book):
    make_book(title="Cheap", price=100)
    make_book(title="Mid", price=200)
    make_book(title="Pricey", price=300)
    r = client.get("/api/books/search", params={"minPrice": 100, "maxPrice": 200, "sort": "price_asc"})
    assert _titles(r) == ["Cheap", "Mid"]


def test_TC_Cat_03_min_greater_than_max_is_rejected(client, make_book):
    make_book()
    assert client.get("/api/books/search", params={"minPrice": 500, "maxPrice": 100}).status_code == 400


def test_TC_Cat_03_negative_price_rejected(client):
    assert client.get("/api/books/search", params={"minPrice": -1}).status_code == 400


# ------------------------------------------------------------------ TC-Cat-04
def test_TC_Cat_04_sort_by_title_and_price(client, make_book):
    make_book(title="Banana", price=300)
    make_book(title="Apple", price=500)
    make_book(title="Cherry", price=100)
    assert _titles(client.get("/api/books", params={"sort": "title_asc"})) == ["Apple", "Banana", "Cherry"]
    assert _titles(client.get("/api/books", params={"sort": "title_desc"})) == ["Cherry", "Banana", "Apple"]
    assert _titles(client.get("/api/books", params={"sort": "price_asc"})) == ["Cherry", "Banana", "Apple"]
    assert _titles(client.get("/api/books", params={"sort": "price_desc"})) == ["Apple", "Banana", "Cherry"]


def test_TC_Cat_04_unknown_sort_option_rejected(client):
    assert client.get("/api/books", params={"sort": "random"}).status_code == 400


def test_pagination_limit_and_offset(client, make_book):
    for i in range(5):
        make_book(title=f"Book {i}")
    r = client.get("/api/books", params={"limit": 2, "offset": 2})
    assert _titles(r) == ["Book 2", "Book 3"]
    assert r.json()["count"] == 5  # total matches, not just this page
    assert client.get("/api/books", params={"limit": 101}).status_code == 400  # boundary: max page size is 100


# ----------------------------------------------------------------- TC-Book-01
def test_TC_Book_01_detail_shows_full_information(client, make_book):
    book = make_book(title="Dune", author="Frank Herbert", isbn="9780441013593", price=399, stock=7)
    r = client.get(f"/api/books/{book.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Dune" and body["isbn"] == "9780441013593"
    assert body["description"] == "About Dune"
    assert body["price"] == 399 and body["availability"] == "In stock"


def test_TC_Book_01_unknown_or_inactive_book_is_404(client, make_book):
    hidden = make_book(is_active=False)
    assert client.get("/api/books/99999").status_code == 404
    assert client.get(f"/api/books/{hidden.id}").status_code == 404


# ----------------------------------------------------------------- security
def test_TC_Sec_05_sql_injection_in_search_is_harmless(client, make_book):
    make_book(title="Dune")
    r = client.get("/api/books/search", params={"q": "' OR 1=1 --"})
    assert r.status_code == 204  # treated as plain text: matches nothing, does not return every book
    assert client.get("/api/books/search", params={"q": "x'; DROP TABLE books; --"}).status_code == 204
    assert client.get("/api/books").json()["count"] == 1  # table still exists


def test_categories_endpoint_lists_categories(client, make_book):
    make_book(category="Science")
    make_book(category="Fiction")
    assert [c["name"] for c in client.get("/api/categories").json()] == ["Fiction", "Science"]
