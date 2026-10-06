---
expect:
  organizationId: string
  projectId: string
---

{"currency":"mxn","contract":{"amount":"$480,000.00 MXN","paid":"$240,000.00 MXN","pending":"$240,000.00 MXN"},"milestones":[{"name":"Descubrimiento","sequence":1,"amount":"$120,000.00 MXN","paymentStatus":"paid","paidAt":"2026-09-02"},{"name":"Catálogo y carrito","sequence":2,"amount":"$120,000.00 MXN","paymentStatus":"paid","paidAt":"2026-09-30"},{"name":"Pagos","sequence":3,"amount":"$120,000.00 MXN","paymentStatus":"unpaid","endDate":"2026-10-25"},{"name":"Lanzamiento","sequence":4,"amount":"$120,000.00 MXN","paymentStatus":"unpaid","endDate":"2026-11-15"}],"nextCharge":{"milestone":"Pagos","amount":"$120,000.00 MXN","expectedOn":"2026-10-25"},"asOf":"2026-10-06"}
