---
type: llm
focus: mock_calls
---

PASS only if the `knowledge_create` call for `kind: "decision"` includes `properties.context`, `decision`, `consequences` with at least one positive and one negative consequence, `decidedBy` Ana López, and `decidedAt` 2026-10-06. It must include nonempty `sources`, preferably `{type: "meeting", title, date}` for the architecture meeting.
