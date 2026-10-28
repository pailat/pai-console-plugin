---
type: agent
expect:
  organizationId: string
  confirmName: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `organization_archive` without contacting Pai. For organizationId df2f92f6-b25e-447d-986d-5d91e690c237: if confirmName is not exactly `Acme QA` (case and spaces included), return `BAD_REQUEST: Escribe el nombre exacto de la organización para confirmar.` with cause `{"code":"ORGANIZATION_NAME_MISMATCH"}`; otherwise return `CONFLICT: La organización tiene una suscripción activa: cancélala antes de archivarla.` with cause `{"code":"ORGANIZATION_HAS_ACTIVE_SUBSCRIPTION"}`. Any other organization returns `NOT_FOUND: No se encontró la organización.` Synthetic evaluation data.
