---
type: llm
---

The accepted `crm_opportunity_win` call must include `delivered: {"closedAt": "2026-09-15"}`.

PASS only if the call carried that `delivered` object with the user's date (not today's date), and the final response says the deal was recorded as already delivered on 2026-09-15 and that no handoff debrief was created. FAIL if it won the deal without `delivered`.
