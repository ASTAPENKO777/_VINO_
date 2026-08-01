"""Single source of truth for order pricing.

Checkout and Order.calculate_totals() used to compute shipping separately,
which let the customer see one total on the checkout page while a different
one was written to the database. Both now go through these helpers.
"""
from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal('0.10')
SHIPPING_COST = Decimal('150')
FREE_SHIPPING_THRESHOLD = Decimal('2000')

_CENTS = Decimal('0.01')


def money(value):
    """Round any amount to two decimal places, half up."""
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


def tax_for(subtotal):
    return money(Decimal(subtotal) * TAX_RATE)


def shipping_for(subtotal):
    """Shipping is free once the subtotal reaches the threshold."""
    if Decimal(subtotal) >= FREE_SHIPPING_THRESHOLD:
        return Decimal('0.00')
    return money(SHIPPING_COST)


def total_for(subtotal):
    subtotal = money(subtotal)
    return money(subtotal + tax_for(subtotal) + shipping_for(subtotal))
