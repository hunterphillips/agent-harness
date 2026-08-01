"""Invoice calculations and text rendering."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


class InvoiceReport:
    def __init__(self, customer: str, tax_rate: Decimal, discount_rate: Decimal = Decimal("0")) -> None:
        self.customer = customer
        self.tax_rate = tax_rate
        self.discount_rate = discount_rate
        self._items: list[tuple[str, int, Decimal]] = []

    def add_item(self, description: str, quantity: int, unit_price: Decimal) -> None:
        if quantity < 1:
            raise ValueError("quantity must be positive")
        if unit_price < 0:
            raise ValueError("unit price cannot be negative")
        self._items.append((description, quantity, unit_price))

    def subtotal(self) -> Decimal:
        gross = sum((price * quantity for _, quantity, price in self._items), Decimal("0"))
        discount = (gross * self.discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        return gross - discount

    def tax(self) -> Decimal:
        gross = sum((price * quantity for _, quantity, price in self._items), Decimal("0"))
        discount = (gross * self.discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        net = gross - discount
        return (net * self.tax_rate).quantize(CENT, rounding=ROUND_HALF_UP)

    def total(self) -> Decimal:
        gross = sum((price * quantity for _, quantity, price in self._items), Decimal("0"))
        discount = (gross * self.discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        net = gross - discount
        tax = (net * self.tax_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        return net + tax

    def render(self) -> str:
        gross = sum((price * quantity for _, quantity, price in self._items), Decimal("0"))
        discount = (gross * self.discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        net = gross - discount
        tax = (net * self.tax_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        total = net + tax
        lines = [f"Invoice for {self.customer}"]
        for description, quantity, price in self._items:
            lines.append(f"{description}: {quantity} x ${price.quantize(CENT):.2f}")
        if discount:
            lines.append(f"Discount: -${discount:.2f}")
        lines.extend([f"Subtotal: ${net:.2f}", f"Tax: ${tax:.2f}", f"Total: ${total:.2f}"])
        return "\n".join(lines)
