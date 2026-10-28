---
type: llm
focus: mock_calls
---

The first `api_design_save` was refused with `API_DESIGN_RULES` (`error-response-schema` at `/paths/~1orders~1{orderId}/get/responses/404`).

PASS only if the last successful `api_design_save`:
1. Still contains GET /orders/{orderId} with both its 200 and its 404 responses.
2. Gives the 404 response's content a schema (for example a shared Error schema or a `$ref`) or an example, instead of deleting the response or its content.
3. Uses expectedRevision 3.
