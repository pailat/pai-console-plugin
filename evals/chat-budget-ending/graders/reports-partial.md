---
type: llm
---

`chat_send` returned status completed, but Pai Agent closed the turn at its per-turn credit budget after reviewing 14 of 37 pages (3 with outdated sources: architecture/overview, guides/refunds, reports/2026-10-weekly; 23 pages left).

PASS only if the final response:
1. Reports the three pages found and says the audit is partial (14 of 37 reviewed, 23 pending).
2. Explains that the turn stopped because it reached its per-turn credit budget, not because of an error.
3. Offers to continue (which charges another turn) and does not claim it already continued.
