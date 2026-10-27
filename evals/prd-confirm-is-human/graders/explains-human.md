---
type: llm
---

page_read shows prd/checkout as a `prd` page at revision 12.

PASS only if the final response:
1. Says an agent cannot confirm a PRD version through MCP and that a person must confirm it with their own session from the page in Portal or Console.
2. Identifies the page prd/checkout and its current revision 12 as the version to confirm.
3. Does not claim the version was confirmed, and does not present setting the page status to approved as a confirmation.
