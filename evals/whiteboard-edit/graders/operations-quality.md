---
type: llm
focus: mock_calls
---

PASS only if the last `whiteboard_update` call satisfies every condition:
1. `path` is the existing literal `diagramas/flujo-de-ventas`, `expectedRevision` is 7 from `whiteboard_read`, `mode` is `edit`, and `idempotencyKey` is present.
2. `operations` contains an `updateNode` whose `ref` is `cotizacion` (or the text “Cotización”) with `label` “Propuesta” and `shape` `diamond`, and a `removeNode` whose `ref` is `lead` (or the text “Lead”).
3. It does not recreate the board: no `content` that redraws existing nodes (“Calificación”, “Cotización”, “Propuesta”, “Lead”), no coordinates or Excalidraw elements, and no operations on nodes the request did not name.
