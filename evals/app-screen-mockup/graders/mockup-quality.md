---
type: llm
focus: mock_calls
---

PASS solo si la llamada a `page_create` cumple todo esto:
1. El `spec` del bloque `view` tiene como raíz (`root`) un elemento `AppShell` con `brand`, `title` («Cobranza» o similar) y `nav` con Inicio, Clientes, Cobranza y Reportes; Cobranza con `active: true`. Cada `icon` es uno del catálogo (por ejemplo home, users, wallet, receipt, reports), nunca uno inventado.
2. Dentro hay tres `Metric` (por cobrar, vencido, cobrado del mes) con valores en MXN ya formateados y una `Table` de facturas vencidas cuyas filas tienen tantas celdas como columnas.
3. Los datos son verosímiles (nombres de clientes y montos, no «Lorem ipsum») y la vista dice que es un mockup (en el título del bloque o de la page).
4. `path` en inglés y kebab-case (por ejemplo `mockups/collections`), `audience` `cliente` y sin `typeSlug`.
5. No hay `className`, `style` ni componentes fuera del catálogo pai-view@1.
