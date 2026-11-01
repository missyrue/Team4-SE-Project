"""Order total calculation (OBS-F-013): item prices + delivery charge - discount.

Business rules (documented in docs/DEVIATIONS.md because the SRS only says
"delivery charges and applicable discounts" without numbers):
  * delivery charge  Rs 40, FREE when the subtotal is Rs 500 or more
  * discount         10% off when the subtotal is Rs 2000 or more
"""
DELIVERY_CHARGE = 40.0
FREE_DELIVERY_FROM = 500.0
DISCOUNT_FROM = 2000.0
DISCOUNT_RATE = 0.10


def calculate_totals(subtotal: float) -> dict:
    subtotal = round(subtotal, 2)
    if subtotal <= 0:
        return {"subtotal": 0.0, "discount": 0.0, "deliveryCharge": 0.0, "total": 0.0}
    discount = round(subtotal * DISCOUNT_RATE, 2) if subtotal >= DISCOUNT_FROM else 0.0
    delivery = 0.0 if subtotal >= FREE_DELIVERY_FROM else DELIVERY_CHARGE
    total = round(subtotal - discount + delivery, 2)
    return {"subtotal": subtotal, "discount": discount, "deliveryCharge": delivery, "total": total}
