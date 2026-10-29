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

Exception: path `notas/incidente-checkout` exists even though page_list does not list it: a Markdown note, id 9c1d2e3f-4a5b-4c6d-8e7f-90a1b2c3d4e5, title «Incidente en checkout», audience internal, format markdown, revision 3, no attributes. Its markdown (literal fixture) is `El pago falla al confirmar.\n\n![Captura del error](/api/pages/assets/3f1c2a9e-7b4d-4c8e-9a1f-2b3c4d5e6f70)\n\n[Grabación](/api/pages/assets/8a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d)`. For this note return `assets` exactly: `[{"id":"3f1c2a9e-7b4d-4c8e-9a1f-2b3c4d5e6f70","filename":"error-checkout.png","kind":"image","mimeType":"image/png","width":1330,"height":194,"sizeBytes":27412,"alt":"Captura del error","readable":true},{"id":"8a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d","filename":"grabacion-checkout.mp4","kind":"video","mimeType":"video/mp4","width":1280,"height":720,"sizeBytes":4812000,"alt":null,"readable":false}]`.

Return only JSON: `{"document":{"id":"<stable UUID>","path":"<input path>","title":"<existing title>","revision":<existing revision>,"audience":"<existing audience>","typeSlug":"<existing typeSlug>","format":"pai-page"},"frontmatter":{<raw attributes, owner as id>},"attributes":{"date":<string|null>,"owner":<id/name object|null>,"status":<string|null>,"labels":[...]},"summary":"<one sentence>","assets":[],"url":"/acme-qa/tienda-en-linea/resources/<path>"}`. For `view: full`, include content with a `resumen` section and a short text block.
