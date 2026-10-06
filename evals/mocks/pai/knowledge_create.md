---
type: agent
expect:
  organizationId: string
  projectId: string
  kind: string
  changeSummary: string
  idempotencyKey: string
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `knowledge_create` del MCP de Pai. Valida lo esencial y responde solo con JSON.

- Si falta `sources` o está vacío: responde el error `FORBIDDEN: SOURCE_REQUIRED: un agente debe citar al menos una fuente.`
- Si `kind` es objective, decision, adr, business_rule o constraint y `status` es `active`: responde el error `FORBIDDEN: HUMAN_CONFIRMS: lo decide una persona; créalo como proposed.`
- Si `kind` es `component` y `properties.c4Type` es `Person`: error `BAD_REQUEST: properties.c4Type: Las personas del C4 son nodos actor.`
- En otro caso, crea el nodo: `{"node":{"id":"<uuid nuevo>","kind":<kind>,"slug":<slug o derivado del título>,"title":<title>,"status":<"proposed" si el kind lo decide una persona, si no status o "active">,"revision":0,"visibility":"internal"},"citation":"kb:<kind>/<slug>@r0","warnings":[],"similar":[],"replayed":false}`.
- Si el mismo `idempotencyKey` ya se usó antes en esta conversación, devuelve la misma respuesta con `"replayed":true`.
