---
type: llm
focus: mock_calls
---

PASS only if the `page_create` call satisfies every condition:
1. The view spec root is an `AppShell` with `brand`, a Collections title, and navigation for Home, Customers, Collections (active), and Reports. Every icon belongs to the catalog, such as home, users, wallet, receipt, or reports.
2. It contains three `Metric` components for outstanding, overdue, and monthly collections, with formatted MXN values, and an overdue-invoices `Table` with matching cell and column counts.
3. Sample customer names and amounts are plausible, and the page or block is labeled as a mockup.
4. `path` uses English kebab-case, such as `mockups/collections`; `audience` is `client`; no `typeSlug` is supplied.
5. No `className`, `style`, or non-catalog components appear.
