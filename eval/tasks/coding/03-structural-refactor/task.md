---
id: coding-03-structural-refactor
type: structural-refactor
weight: 1.0
---
## Task Prompt

Refactor `InvoiceReport` so its repeated subtotal, discount, tax, and total calculation lives in one private `_totals` method. The public methods `add_item`, `subtotal`, `tax`, `total`, and `render` must keep their current names, signatures, and behavior, and each calculation-facing public method must use the shared helper. Do not edit tests or add dependencies. Keep the change confined to `invoice/report.py`.
