---
type: llm
focus: mock_calls
---

PASS only if the last `whiteboard_update` call satisfies every condition:
1. `path` is the existing literal `diagramas/flujo-de-ventas`, `expectedRevision` is 7 from `whiteboard_read`, and `idempotencyKey` is present.
2. `content` is `{graph}` or `{mermaid}`, without coordinates (`x`, `y`, `width`, `height`) or Excalidraw elements.
3. It adds “Negociación” and “Cierre” using new ids distinct from existing `lead`, `calificacion`, and `cotizacion`.
4. An edge connects existing `cotizacion` (or its text “Cotización”) to “Negociación”, then another connects “Negociación” to “Cierre”. It does not recreate “Cotización”.
