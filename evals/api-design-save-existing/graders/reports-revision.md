---
type: llm
---

`api_design_save` accepted expectedRevision 3 and returned revision 4.

PASS only if the final response:
1. Says GET /orders/{orderId} was added to the existing Orders API design (not a new design).
2. Reports revision 4 or the citation `kb:api/orders-api@r4`.
3. Does not claim the real Orders service now implements the endpoint.
