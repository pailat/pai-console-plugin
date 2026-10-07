---
type: llm
focus: mock_calls
---

`payment_list` devolvió: contrato $480,000 MXN, cobrado $240,000, pendiente $240,000, cuatro hitos de $120,000 (Descubrimiento y Catálogo y carrito pagados; Pagos y Lanzamiento sin pagar) y siguiente cobro «Pagos» el 2026-10-25, al 2026-10-06.

PASS solo si en la llamada a `view_render`:
1. Todas las cifras y fechas del `spec` coinciden con esos datos o se calculan directamente de ellos. Son válidos, por ejemplo, «50 %» cobrado, «2 de 4 hitos» o la suma de montos. FAIL solo si aparece una cifra o una fecha que no está en los datos ni se calcula de ellos.
2. Hay al menos un `Metric` con un monto ya formateado (por ejemplo «$240,000» con unidad MXN, o «$240,000 MXN»).
3. La vista dice la fecha de corte 2026-10-06 o que los datos vienen de payment_list.
4. Usa solo componentes del catálogo pai-view@1 (por ejemplo Section, Grid, Metric, BarList, Table, Stages, StatusBadge, Progress, Item); los estados de pago, si aparecen, van con StatusBadge o StatusDot, no con colores.
