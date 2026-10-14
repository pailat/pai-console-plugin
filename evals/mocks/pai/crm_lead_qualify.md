---
type: agent
expect:
  leadId: string
  expectedRevision: number
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `crm_lead_qualify` del MCP de Pai para una persona **sin** el permiso `crm:join` (`crm_access_get` da crm:access, crm:edit, crm:convert, crm:revenue). Responde solo con JSON o con un error.

- Si `expectedRevision` no es 4: error `CONFLICT: El lead cambió; vuelve a leerlo.`
- Si `workspace.mode` es `link_existing`: error `FORBIDDEN: No tienes permiso para ligar el lead a una organización existente: crea la organización desde el lead.`
- Si `workspace.mode` es `create_from_lead`: éxito; crea una organización **nueva** «Globex» (id nuevo, distinto de 6e5d4c3b-2a19-4807-b6c5-d4e3f2a1b0c9) y el proyecto «Descubrimiento» en borrador. Responde `{"lead":{"id":"3f0c9a7e-2b1d-4c5e-8f6a-7b8c9d0e1f2a","stage":"<qualified si es crm_lead_qualify, si no contacted>","revision":5,"organizationId":"<id nuevo>"},"workspace":{"organizationId":"<id nuevo>","created":true,"member":false}}` (con `opportunity` si es crm_lead_qualify).
- Sin `workspace` en crm_lead_qualify: error `BAD_REQUEST: El lead no tiene espacio de trabajo; manda workspace.`
