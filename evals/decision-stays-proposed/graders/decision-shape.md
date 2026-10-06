---
type: llm
focus: mock_calls
---

PASS solo si la llamada a `knowledge_create` con `kind: "decision"` lleva en `properties` `context`, `decision`, `consequences` con al menos una consecuencia positiva y una negativa, `decidedBy` (Ana López) y `decidedAt` (2026-10-06); y si lleva `sources` no vacío, de preferencia `{type: "meeting", title, date}` por la reunión de arquitectura.
