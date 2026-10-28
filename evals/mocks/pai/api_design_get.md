---
type: agent
expect:
  organizationId: string
  apiDesignId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `api_design_get` without contacting Pai. Only apiDesignId 5a1c9e2b-7d3f-4b6a-8c1e-2f4a6b8d0c13 exists; any other id returns `NOT_FOUND: No se encontró el diseño de API.`

The design is "Orders API", revision 3, citation kb:api/orders-api@r3. Its normalized OpenAPI 3.1 document has info {title "Orders API", version "1.0.0"}, a path /orders with GET (operationId listOrders, 200 returning an array of Order) and POST (operationId createOrder, 201 returning Order), and components.schemas.Order (object with required id string and total integer, carrying "x-pai-entity": "entity/order").

With include "document" return JSON `{"apiDesign":{"id":...,"title":"Orders API","revision":3,"citation":"kb:api/orders-api@r3"},"document":<the full document>}`. With include "view" or omitted, return `{"apiDesign":{...},"view":{"operations":[...]},"links":[{"kind":"entity","ref":"entity/order","pointer":"/components/schemas/Order","node":{"kind":"entity","slug":"order"}}]}`. All names and identifiers here are synthetic evaluation data.
