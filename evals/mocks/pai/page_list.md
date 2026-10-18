---
type: agent
expect:
  organizationId: string
  projectId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `page_list`. The project contains exactly these pages. Titles and labels below are literal Spanish fixture data:

| path | title | audience | revision | typeSlug | attributes |
|---|---|---|---|---|---|
| `architecture/overview` | Arquitectura general | internal | 4 | architecture | `{"status":"approved","date":"2026-09-20","labels":["arquitectura"],"owner":{"id":"7b1e4c2a-5d3f-4a6b-9c8d-0e1f2a3b4c5d","name":"Laura Méndez"}}` |
| `processes/payment-reconciliation` | Conciliación de pagos | internal | 6 | process | `{"status":"in_review","date":"2026-10-08","labels":["pagos","finanzas"]}` |
| `guides/refunds` | Guía de reembolsos | client | 3 | guide | `{"status":"in_review","date":"2026-10-02","labels":["pagos"],"owner":{"id":"3c9d8e7f-1a2b-4c3d-8e4f-5a6b7c8d9e0f","name":"Diego Ruiz"}}` |
| `reports/2026-10-weekly` | Reporte semanal | internal | 2 | report | `{"status":"draft","labels":["reportes"]}` |
| `notes/kickoff` | Notas del kickoff | client | 1 | — | — |

Apply supplied filters: status matches any listed value; labels match any page label case-insensitively; owner matches case-insensitive name or id; inclusive dateFrom/dateTo exclude undated pages; also apply audience and pathPrefix. Sort by path (default), newest date first, or status (draft, in_review, approved, archived); missing values go last.

Return only JSON with items (stable UUID, path, title, revision, updatedAt 2026-10-10T12:00:00.000Z, typeSlug, audience, openCommentCount 0, attributes when present), resourcesUrl `/portal/organization/projects/<projectId>/resources`, hasMore false and nextCursor null.
