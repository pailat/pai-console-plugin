---
type: agent
expect:
  serviceAccountId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `iam_service_account_get` without contacting Pai. For serviceAccountId 6f1d2c3e-4a5b-4c6d-8e7f-a1b2c3d4e5f6 return `{"id":"6f1d2c3e-4a5b-4c6d-8e7f-a1b2c3d4e5f6","organizationId":"df2f92f6-b25e-447d-986d-5d91e690c237","userId":"0b9a8c7d-6e5f-4a3b-9c2d-1e0f9a8b7c6d","ownerUserId":null,"name":"ci-reporter","description":"Synthetic reporting job","disabledAt":null,"createdAt":"2026-10-01T15:00:00.000Z","updatedAt":"2026-10-01T15:00:00.000Z"}`. Any other id returns `NOT_FOUND` with cause `{"code":"SERVICE_ACCOUNT_NOT_FOUND"}`. Synthetic evaluation data.
