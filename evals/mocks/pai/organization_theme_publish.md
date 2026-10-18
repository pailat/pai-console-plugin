---
type: agent
expect:
  organizationId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai MCP `organization_theme_publish`. Without a draft saved earlier in this conversation and without an explicit version, return `NOT_FOUND: No hay un borrador del tema que publicar.` If the latest draft had contrast issues, return `BAD_REQUEST: El tema no se puede publicar: no cumple el contraste AA o tiene problemas.` with one line per issue. Otherwise return only `{"organizationId":"df2f92f6-b25e-447d-986d-5d91e690c237","version":<draft or requested version>,"status":"published","publishedAt":"2026-10-13T18:05:00.000Z"}`.
