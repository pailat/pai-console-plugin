---
type: llm
---

PASS only if the final response:
1. Says the decision remains **proposed**, not active.
2. Explains that a person activates it in Portal or Console.
3. Provides `kb:decision/<slug>@r0` or the node slug.

FAIL if it claims the decision is active or effective.
