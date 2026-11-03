---
type: agent
expect:
  hostId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `connection_get` without contacting Pai. For hostId 9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b return `{"id":"9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b","organizationId":"df2f92f6-b25e-447d-986d-5d91e690c237","nativeId":"build-box-qa","label":"build-box-qa","status":"active","revision":4,"keyEpoch":1}`. Any other id returns `NOT_FOUND` with cause `{"code":"CONNECTION_NOT_FOUND"}`. Synthetic evaluation data.
