"""PLACEHOLDER: Aanya replaces this file in feature/inventory-service."""


class InsufficientStock(Exception):
    def __init__(self, book_id: int):
        super().__init__(f"Insufficient stock for book {book_id}")
        self.book_id = book_id


def deduct_stock(db, items):
    raise NotImplementedError("inventory service not merged yet")


def restore_stock(db, items):
    raise NotImplementedError("inventory service not merged yet")
