---
type: agent
expect:
  id: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `agent_routine_delete` without contacting Pai. For id 7b8c9d0e-1f2a-4b3c-8d4e-5f6a7b8c9d0e return `{"id":"7b8c9d0e-1f2a-4b3c-8d4e-5f6a7b8c9d0e","deleted":true}`. Any other id returns `NOT_FOUND` with the message the server uses for a link that is not the caller's. Synthetic evaluation data.
