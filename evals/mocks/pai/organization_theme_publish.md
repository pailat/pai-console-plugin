---
type: agent
expect:
  organizationId: string
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `organization_theme_publish` del MCP de Pai. Si en esta conversación no se guardó antes un borrador con `organization_theme_save_draft` y no viene `version`, responde el error `NOT_FOUND: No hay un borrador del tema que publicar.` Si el último borrador guardado tenía issues de contraste, responde el error `BAD_REQUEST: El tema no se puede publicar: no cumple el contraste AA o tiene problemas.` con una línea por issue. Si no, responde solo con JSON `{"organizationId":"df2f92f6-b25e-447d-986d-5d91e690c237","version":<la del borrador o la indicada>,"status":"published","publishedAt":"2026-10-13T18:05:00.000Z"}`.
