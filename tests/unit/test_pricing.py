"""UNIT tests - order total calculation (OBS-F-013, TC-Order-02) incl. boundaries."""
import pytest

from app.services.pricing import calculate_totals


def test_small_order_pays_delivery_no_discount():
    assert calculate_totals(200) == {"subtotal": 200.0, "discount": 0.0, "deliveryCharge": 40.0, "total": 240.0}


@pytest.mark.parametrize(
    "subtotal, delivery",
    [(499.99, 40.0), (500.0, 0.0), (500.01, 0.0)],  # boundary: free delivery starts AT 500
)
def test_free_delivery_boundary(subtotal, delivery):
    assert calculate_totals(subtotal)["deliveryCharge"] == delivery


@pytest.mark.parametrize(
    "subtotal, discount",
    [(1999.99, 0.0), (2000.0, 200.0), (3000.0, 300.0)],  # boundary: 10% discount starts AT 2000
)
def test_discount_boundary(subtotal, discount):
    assert calculate_totals(subtotal)["discount"] == discount


def test_large_order_total_is_subtotal_minus_discount():
    assert calculate_totals(2000)["total"] == 1800.0


def test_empty_cart_totals_are_zero():
    assert calculate_totals(0) == {"subtotal": 0.0, "discount": 0.0, "deliveryCharge": 0.0, "total": 0.0}


def test_rounding_to_two_decimals():
    assert calculate_totals(333.333)["subtotal"] == 333.33
