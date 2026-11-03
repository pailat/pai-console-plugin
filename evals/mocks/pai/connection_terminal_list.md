---
type: agent
expect:
  hostId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `connection_terminal_list` without contacting Pai. For hostId 9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b return `{"items":[{"id":"3c4d5e6f-7a8b-4c9d-a0e1-f2a3b4c5d6e7","organizationId":"df2f92f6-b25e-447d-986d-5d91e690c237","hostId":"9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b","openedByUserId":null,"shell":"bash","state":"detached","cols":120,"rows":32,"epoch":2,"createdAt":"2026-11-02T15:00:00.000Z","attachedAt":"2026-11-02T15:00:05.000Z","detachedAt":"2026-11-02T15:10:00.000Z","lastSeenAt":"2026-11-02T15:10:00.000Z","expiresAt":"2026-11-03T03:00:00.000Z","closedAt":null,"closeReason":null},{"id":"5d6e7f8a-9b0c-4d1e-b2f3-a4b5c6d7e8f9","organizationId":"df2f92f6-b25e-447d-986d-5d91e690c237","hostId":"9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b","openedByUserId":null,"shell":"bash","state":"closed","cols":100,"rows":30,"epoch":2,"createdAt":"2026-11-01T15:00:00.000Z","attachedAt":"2026-11-01T15:00:05.000Z","detachedAt":null,"lastSeenAt":"2026-11-01T15:20:00.000Z","expiresAt":"2026-11-02T03:00:00.000Z","closedAt":"2026-11-01T15:20:00.000Z","closeReason":"exited"}]}`. Any other id returns `NOT_FOUND` with cause `{"code":"CONNECTION_NOT_FOUND"}`. Synthetic evaluation data.
