---
type: agent
expect:
  leadId: string
  expectedRevision: number
abort_when: "Never abort; always respond as the server."
---

Act as Pai MCP `crm_lead_workspace_open` for a user without crm:join (crm_access_get returns crm:access, crm:edit, crm:convert and crm:revenue). Return JSON or an error.

- If expectedRevision is not 4: `CONFLICT: El lead cambió; vuelve a leerlo.`
- If workspace.mode is link_existing: `FORBIDDEN: No tienes permiso para ligar el lead a una organización existente: crea la organización desde el lead.`
- If workspace.mode is create_from_lead: succeed by creating a NEW Globex organization with a UUID different from 6e5d4c3b-2a19-4807-b6c5-d4e3f2a1b0c9 and a draft Discovery project. Return `{"lead":{"id":"3f0c9a7e-2b1d-4c5e-8f6a-7b8c9d0e1f2a","stage":"<qualified for crm_lead_qualify; contacted otherwise>","revision":5,"organizationId":"<new id>"},"workspace":{"organizationId":"<new id>","created":true,"member":false}}`, including an opportunity for crm_lead_qualify.
- crm_lead_qualify without workspace: `BAD_REQUEST: El lead no tiene espacio de trabajo; manda workspace.`
