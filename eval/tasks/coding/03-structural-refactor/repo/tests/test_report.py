from __future__ import annotations

import unittest
from decimal import Decimal

from invoice import InvoiceReport


class InvoiceReportTests(unittest.TestCase):
    def test_empty_invoice(self) -> None:
        report = InvoiceReport("Ada", Decimal("0.10"))
        self.assertEqual(report.subtotal(), Decimal("0"))
        self.assertEqual(report.tax(), Decimal("0.00"))
        self.assertEqual(report.total(), Decimal("0.00"))

    def test_calculates_discount_tax_and_total(self) -> None:
        report = InvoiceReport("Ada", Decimal("0.0825"), Decimal("0.10"))
        report.add_item("Support", 3, Decimal("19.99"))
        report.add_item("Setup", 1, Decimal("40.00"))
        self.assertEqual(report.subtotal(), Decimal("89.97"))
        self.assertEqual(report.tax(), Decimal("7.42"))
        self.assertEqual(report.total(), Decimal("97.39"))

    def test_rounds_discount_and_tax_half_up(self) -> None:
        report = InvoiceReport("Ravi", Decimal("0.05"), Decimal("0.05"))
        report.add_item("Part", 1, Decimal("0.10"))
        self.assertEqual(report.subtotal(), Decimal("0.09"))
        self.assertEqual(report.tax(), Decimal("0.00"))

    def test_render_includes_items_and_totals(self) -> None:
        report = InvoiceReport("Mina", Decimal("0.10"), Decimal("0.25"))
        report.add_item("Cable", 2, Decimal("8.00"))
        self.assertEqual(
            report.render(),
            "\n".join(
                [
                    "Invoice for Mina",
                    "Cable: 2 x $8.00",
                    "Discount: -$4.00",
                    "Subtotal: $12.00",
                    "Tax: $1.20",
                    "Total: $13.20",
                ]
            ),
        )

    def test_rejects_invalid_items(self) -> None:
        report = InvoiceReport("Kai", Decimal("0"))
        with self.assertRaises(ValueError):
            report.add_item("Bad quantity", 0, Decimal("1"))
        with self.assertRaises(ValueError):
            report.add_item("Bad price", 1, Decimal("-1"))


if __name__ == "__main__":
    unittest.main()
