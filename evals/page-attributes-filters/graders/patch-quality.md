---
type: llm
focus: mock_calls
---

PASS only if all conditions hold:
1. `page_list` filters server-side using `status: ["in_review"]` and `labels: ["pagos"]`, rather than fetching everything to filter manually.
2. The successful `page_frontmatter_update` targets `processes/payment-reconciliation`; its `frontmatter` contains only changes: `status: "approved"`, `date: "2026-10-12"`, and `owner: "7b1e4c2a-5d3f-4a6b-9c8d-0e1f2a3b4c5d"` from `milestone_owner_options`, not the person's name. It neither resends nor deletes `labels`.
3. `expectedRevision` is 6, as returned by `page_list` or `page_read`.
4. It never calls `page_update` or rewrites the content.
