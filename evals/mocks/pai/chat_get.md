---
type: agent
expect:
  sessionId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `chat_get` without contacting Pai. Session 3e5a7c9b-1d2f-4a6b-8c0e-2f4a6b8d0e1c is the user's active chat "Limpieza de borradores" in organization df2f92f6-b25e-447d-986d-5d91e690c237. Before any chat_send it has one earlier completed turn and no pending approvals. After chat_send, its latest assistant turn asks to approve page_delete on drafts/old-pricing (approval id appr-7f3c, state approval-requested). Any other session returns `NOT_FOUND: No encontramos el chat.` Synthetic evaluation data.
