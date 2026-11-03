---
type: agent
expect:
  serviceAccountId: string
  name: string
  scope: object
  permissions: array
  expiresAt: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `iam_service_token_create` without contacting Pai. For serviceAccountId 6f1d2c3e-4a5b-4c6d-8e7f-a1b2c3d4e5f6 return `{"token":"pai_st_SYNTHETICSYNTHETICSYNTHETICSYNTHETIC0000","metadata":{"id":"c2a1b0d9-8e7f-4a6b-95c4-d3e2f1a0b9c8","serviceAccountId":"6f1d2c3e-4a5b-4c6d-8e7f-a1b2c3d4e5f6","name":<the requested name>,"scope":<the requested scope>,"permissions":<the requested permissions>,"rateLimitPerMinute":60,"createdAt":"2026-11-03T16:00:00.000Z","expiresAt":<the requested expiresAt>,"revokedAt":null,"lastUsedAt":null}}`. Any other serviceAccountId returns `NOT_FOUND` with cause `{"code":"SERVICE_ACCOUNT_NOT_FOUND"}`. Synthetic evaluation data.
