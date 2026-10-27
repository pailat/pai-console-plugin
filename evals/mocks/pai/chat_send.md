---
type: agent
expect:
  sessionId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `chat_send` without contacting Pai. Only sessionId 3e5a7c9b-1d2f-4a6b-8c0e-2f4a6b8d0e1c exists and is active.

- A call whose `message` asks to audit or review every page (any language) returns the per-turn budget ending: `{"turnId":"5d7f9b1c-3e5a-4c7e-9a1b-3d5f7a9c1e3b","status":"completed","reply":"Revisé 14 de 37 páginas: 3 tienen fuentes vencidas (architecture/overview, guides/refunds, reports/2026-10-weekly). Faltan 23 páginas por revisar.\n\nCerré aquí este turno al llegar a su presupuesto de créditos. Si quieres, pídeme que siga y continúo desde este punto.","pendingApprovals":[],"session":{"id":"3e5a7c9b-1d2f-4a6b-8c0e-2f4a6b8d0e1c","status":"active"}}`. A second call with any continuation message returns the same shape with 14 more pages reviewed.
- Any other call with `message` (no approvalResponse) returns `{"turnId":"8b0d2f4a-6c8e-4a1b-9d3f-5a7c9e1b3d5f","status":"completed","reply":"Para archivar ese borrador necesito eliminar la page drafts/old-pricing. ¿Lo apruebas?","pendingApprovals":[{"id":"appr-7f3c","toolName":"page_delete","input":{"path":"drafts/old-pricing"}}],"session":{"id":"3e5a7c9b-1d2f-4a6b-8c0e-2f4a6b8d0e1c","status":"active"}}`.
- A call with `approvalResponse` id appr-7f3c returns `{"turnId":"1c3e5a7b-9d0f-4b2c-8e4a-6b8d0f2a4c6e","status":"completed","reply":"Eliminé la page.","pendingApprovals":[],"session":{"id":"3e5a7c9b-1d2f-4a6b-8c0e-2f4a6b8d0e1c","status":"active"}}`; any other approval id returns `BAD_REQUEST: La aprobación indicada no está pendiente en el último turno del chat.`

All names and identifiers here are synthetic evaluation data.
