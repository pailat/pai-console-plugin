---
type: llm
focus: mock_calls
---

PASS solo si se cumple todo esto:
1. La llamada a `page_list` filtra en el servidor con `status: ["in_review"]` y `labels: ["pagos"]` (no lista todo para filtrar a mano), y la respuesta final a la persona nombra las dos pages en revisión con esa etiqueta: «Conciliación de pagos» y «Guía de reembolsos».
2. La llamada a `page_frontmatter_update` que tuvo éxito es sobre `processes/payment-reconciliation`, con `frontmatter` que lleva solo lo que cambia: `status: "approved"`, `date: "2026-10-12"` y `owner: "7b1e4c2a-5d3f-4a6b-9c8d-0e1f2a3b4c5d"` (el id de Laura Méndez en `milestone_owner_options`, no su nombre). No reenvía ni borra `labels`.
3. Lleva `expectedRevision: 6`, la revisión que dieron `page_list` o `page_read`.
4. No llamó a `page_update` ni reescribió el contenido.
