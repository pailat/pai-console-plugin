---
type: agent
expect:
  organizationId: string
  apiDesignId: string
  expectedRevision: number
  source: string
  changeSummary: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `api_design_save` without contacting Pai. Only apiDesignId 5a1c9e2b-7d3f-4b6a-8c1e-2f4a6b8d0c13 exists. A different expectedRevision than 3 returns `CONFLICT` with cause `{"code":"REVISION","current":{"revision":3}}`. A source that is not a complete OpenAPI 3.1 document (missing openapi, info or the existing /orders operations) returns `BAD_REQUEST` with cause `{"code":"OPENAPI_INVALID","issues":[{"path":"/","code":"incomplete","message":"El documento debe ser OpenAPI 3.1 completo."}]}`.

If the source's new GET /orders/{orderId} operation (or any operation) has a 404 or other 4XX response with content but neither a schema nor an example, return `BAD_REQUEST: El diseño no cumple las reglas de integridad.` with cause `{"code":"API_DESIGN_RULES","findings":[{"ruleId":"error-response-schema","severity":"error","pointer":"/paths/~1orders~1{orderId}/get/responses/404","message":"Una respuesta de error con contenido declara un schema o un ejemplo."}]}` and write nothing.

Otherwise return `{"findings":[],"apiDesign":{"id":"5a1c9e2b-7d3f-4b6a-8c1e-2f4a6b8d0c13","title":"Orders API","revision":4,"citation":"kb:api/orders-api@r4","counts":{"paths":2,"operations":3,"schemas":1}},"unchanged":false,"replayed":false,"warnings":[]}`. A second accepted call returns CONFLICT because the current revision is 4. All names and identifiers here are synthetic evaluation data.
