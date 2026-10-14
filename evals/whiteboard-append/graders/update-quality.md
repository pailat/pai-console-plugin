---
type: llm
focus: mock_calls
---

PASS solo si la llamada a `whiteboard_update` (la última, si hubo varias) cumple todo esto:
1. `path` es `diagramas/flujo-de-ventas`, `expectedRevision` es `7` (la `revision` de `whiteboard_read`) e `idempotencyKey` está presente.
2. `content` es `{graph}` o `{mermaid}`, sin coordenadas (`x`, `y`, `width`, `height`) ni elementos de Excalidraw.
3. Agrega «Negociación» y «Cierre» como nodos nuevos con ids que no repiten los de la pizarra (`lead`, `calificacion`, `cotizacion`).
4. Hay una arista de la cotización existente (por su id `cotizacion` o por su texto «Cotización») a «Negociación», y otra de «Negociación» a «Cierre». No vuelve a crear «Cotización» como nodo nuevo.
