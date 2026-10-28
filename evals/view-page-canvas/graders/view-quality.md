---
type: llm
focus: mock_calls
---

PASS only if the `page_create` call satisfies every condition:
1. `path` uses English kebab-case within a folder, such as `dashboards/sales`, without accents or spaces.
2. `content` has `schemaVersion: 1`, `componentSetVersion: "pai-core-v1"`, `layout: "canvas"`, and a view block with spec `root` and `elements`.
3. Only pai-view@1 components are used. At least two `Metric` components have formatted values (extra metrics directly calculated from the supplied data, such as an average ticket, are fine), and a `Chart` of `kind: "line"` has four categories and one series of four values. No `className`, `style`, or HTML.
4. Content includes cutoff date 2026-10-04.
5. `summary` is at most 80 characters and `idempotencyKey` is present.
