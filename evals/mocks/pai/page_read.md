---
type: agent
expect:
  organizationId: string
  projectId: string
  path: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `page_read`. Reuse the exact revision, title, audience, typeSlug and attributes returned by page_list earlier in this conversation. A missing page returns `NOT_FOUND: No se encontró la page.`

Return only JSON: `{"document":{"id":"<stable UUID>","path":"<input path>","title":"<existing title>","revision":<existing revision>,"audience":"<existing audience>","typeSlug":"<existing typeSlug>","format":"pai-page"},"frontmatter":{<raw attributes, owner as id>},"attributes":{"date":<string|null>,"owner":<id/name object|null>,"status":<string|null>,"labels":[...]},"summary":"<one sentence>","url":"/portal/organization/projects/<projectId>/resources/<path>"}`. For `view: full`, include content with a `resumen` section and a short text block.
