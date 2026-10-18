---
type: llm
focus: mock_calls
---

`payment_list` returned a $480,000 MXN contract, $240,000 collected, $240,000 outstanding, and four $120,000 milestones. “Descubrimiento” and “Catálogo y carrito” are paid; “Pagos” and “Lanzamiento” are unpaid. The next collection is “Pagos” on 2026-10-25, with data as of 2026-10-06.

PASS only if the `view_render` call satisfies every condition:
1. Every spec amount and date comes from or is directly calculated from those data. Examples include 50% collected, 2 of 4 milestones, or sums. FAIL only for unsupported amounts or dates.
2. At least one `Metric` contains a formatted amount, such as $240,000 with MXN as its unit.
3. The view states the 2026-10-06 cutoff or attributes the data to payment_list.
4. Only pai-view@1 catalog components are used. Payment states use StatusBadge or StatusDot, not color alone.
