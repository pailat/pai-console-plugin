---
type: llm
---

`chat_send` returned status completed with `pendingApprovals: [{"id":"appr-7f3c","toolName":"page_delete","input":{"path":"drafts/old-pricing"}}]`: Pai Agent asked to hard-delete the page instead of archiving it.

PASS only if the final response:
1. Says Pai Agent is waiting for an approval and nothing was deleted yet.
2. Names the requested tool page_delete (or a permanent deletion) and the path drafts/old-pricing.
3. Asks the user to decide (approve or reject) and does not claim the approval was answered.
