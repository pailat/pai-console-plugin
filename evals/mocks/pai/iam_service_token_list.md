---
type: agent
expect:
  serviceAccountId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `iam_service_token_list` without contacting Pai. For serviceAccountId 6f1d2c3e-4a5b-4c6d-8e7f-a1b2c3d4e5f6 return `{"tokens":[]}`; no token value is ever part of a list. Any other id returns `NOT_FOUND` with cause `{"code":"SERVICE_ACCOUNT_NOT_FOUND"}`. Synthetic evaluation data.
