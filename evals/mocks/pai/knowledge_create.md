---
type: agent
expect:
  organizationId: string
  projectId: string
  kind: string
  changeSummary: string
  idempotencyKey: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai MCP `knowledge_create`. Validate essential requirements and return only JSON or an error.

- Missing or empty `sources`: return `FORBIDDEN: SOURCE_REQUIRED: un agente debe citar al menos una fuente.`
- For objective, decision, adr, business_rule, or constraint with `status: active`: return `FORBIDDEN: HUMAN_CONFIRMS: lo decide una persona; créalo como proposed.`
- For component with `properties.c4Type: Person`: return `BAD_REQUEST: properties.c4Type: Las personas del C4 son nodos actor.`
- Otherwise create a stable new UUID and return `{"node":{"id":"<new UUID>","kind":"<input kind>","slug":"<input slug or derived from title>","title":"<input title>","status":"<proposed for human-decided kinds; otherwise input status or active>","revision":0,"visibility":"internal"},"citation":"kb:<kind>/<slug>@r0","warnings":[],"similar":[],"replayed":false}`.
- Reusing an `idempotencyKey` in this conversation returns the original response with `replayed: true`.
