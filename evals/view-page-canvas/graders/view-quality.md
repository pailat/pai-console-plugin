---
type: llm
focus: mock_calls
---

PASS solo si la llamada a `page_create` cumple todo esto:
1. `path` en inglés, kebab-case y en carpeta (por ejemplo `dashboards/sales`), sin acentos ni espacios.
2. `content` con `schemaVersion: 1`, `componentSetVersion: "pai-core-v1"`, `layout: "canvas"` y un bloque `view` cuyo `spec` tiene `root` y `elements`.
3. El spec solo usa componentes del catálogo pai-view@1 (Stack, Grid, Metric, Chart, Section, Card, Table…). Hay dos `Metric` con los valores ya formateados y una `Chart` `kind: "line"` con 4 categorías y una serie de 4 valores. No hay `className`, `style` ni HTML.
4. La fecha de corte 2026-10-04 aparece en el contenido.
5. `summary` de 80 caracteres o menos e `idempotencyKey` presente.
