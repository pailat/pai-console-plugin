---
type: agent
expect:
  organizationId: string
  projectId: string
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `page_list` del MCP de Pai 0.2.5. El proyecto tiene exactamente estas pages:

| path | title | audience | revision | typeSlug | attributes |
|---|---|---|---|---|---|
| `architecture/overview` | Arquitectura general | internal | 4 | architecture | `{"status":"approved","date":"2026-09-20","labels":["arquitectura"],"owner":{"id":"7b1e4c2a-5d3f-4a6b-9c8d-0e1f2a3b4c5d","name":"Laura Méndez"}}` |
| `processes/payment-reconciliation` | Conciliación de pagos | internal | 6 | process | `{"status":"in_review","date":"2026-10-08","labels":["pagos","finanzas"]}` |
| `guides/refunds` | Guía de reembolsos | client | 3 | guide | `{"status":"in_review","date":"2026-10-02","labels":["pagos"],"owner":{"id":"3c9d8e7f-1a2b-4c3d-8e4f-5a6b7c8d9e0f","name":"Diego Ruiz"}}` |
| `reports/2026-10-weekly` | Reporte semanal | internal | 2 | report | `{"status":"draft","labels":["reportes"]}` |
| `notes/kickoff` | Notas del kickoff | client | 1 | — | — |

Aplica los filtros que vengan: `status` (alguno de la lista), `labels` (la page tiene alguna, sin distinguir mayúsculas), `owner` (nombre sin distinguir mayúsculas, o id), `dateFrom`/`dateTo` (AAAA-MM-DD incluidos; las pages sin fecha quedan fuera), `audience`, `pathPrefix`. Ordena por `sort`: `path` (por defecto), `date` (más reciente primero) o `status` (draft, in_review, approved, archived); sin valor, al final.

Responde solo con JSON: `{"items":[{"id":"<uuid inventado y estable>","path","title","revision","updatedAt":"2026-10-10T12:00:00.000Z","typeSlug","audience","openCommentCount":0,"attributes"?}],"resourcesUrl":"/portal/organization/projects/<projectId>/resources","hasMore":false,"nextCursor":null}`. Incluye `attributes` solo en las pages que tienen alguno.
