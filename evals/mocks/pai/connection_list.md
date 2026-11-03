---
type: agent
expect:
  scope: string
  query: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `connection_list` without contacting Pai. The tool takes no organizationId. If the query is empty or matches "build-box-qa" (case-insensitive) return `{"items":[{"id":"9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b","organizationId":"df2f92f6-b25e-447d-986d-5d91e690c237","nativeId":"build-box-qa","label":"build-box-qa","status":"active","revision":4,"keyEpoch":1}],"total":1,"pageIndex":0,"pageSize":25}`; otherwise return `{"items":[],"total":0,"pageIndex":0,"pageSize":25}`. Synthetic evaluation data.
