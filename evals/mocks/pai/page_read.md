---
type: agent
expect:
  organizationId: string
  projectId: string
  path: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `page_read`. Reuse the exact revision, title, audience, typeSlug and attributes returned by page_list earlier in this conversation. A missing page returns `NOT_FOUND: No se encontró la page.`

Exception: path `prd/checkout` exists even though page_list does not list it: id 4f6a8c0e-2b4d-4f6a-8c0e-2b4d6f8a0c2e, title «PRD de checkout», typeSlug `prd`, audience client, format pai-page, revision 12, attributes all null with empty labels. Its content has sections `resumen`, `requisitos` and `metricas` with short text blocks. Never return confirmation fields: MCP does not expose them.

Return only JSON: `{"document":{"id":"<stable UUID>","path":"<input path>","title":"<existing title>","revision":<existing revision>,"audience":"<existing audience>","typeSlug":"<existing typeSlug>","format":"pai-page"},"frontmatter":{<raw attributes, owner as id>},"attributes":{"date":<string|null>,"owner":<id/name object|null>,"status":<string|null>,"labels":[...]},"summary":"<one sentence>","url":"/portal/organization/projects/<projectId>/resources/<path>"}`. For `view: full`, include content with a `resumen` section and a short text block.
