---
type: agent
expect:
  hostId: string
  terminalId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `connection_terminal_terminate` without contacting Pai. For hostId 9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b and terminalId 3c4d5e6f-7a8b-4c9d-a0e1-f2a3b4c5d6e7 return the terminal with `"state":"closing"` and `"closeReason":"terminated"` (same other fields as the list: shell bash, cols 120, rows 32, epoch 2, closedAt null). For terminalId 5d6e7f8a-9b0c-4d1e-b2f3-a4b5c6d7e8f9 return it unchanged with `"state":"closed"` and `"closeReason":"exited"`. Any other id returns `NOT_FOUND` with cause `{"code":"CONNECTION_NOT_FOUND"}`. Synthetic evaluation data.
