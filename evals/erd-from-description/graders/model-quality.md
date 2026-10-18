---
type: llm
focus: mock_calls
---

PASS only if the `knowledge_create` calls satisfy every condition:
1. A `data_model` and at least two `entity` nodes (author and book) have English kebab-case slugs.
2. Every entity references the model in `properties.dataModel`. Every column declares a snake_case `name`, a closed-vocabulary `type` (uuid, text, integer, bigint, numeric, real, boolean, date, time, timestamptz, interval, jsonb, bytea, vector, enum), and boolean `nullable`, `primaryKey`, and `unique`. No `varchar`.
3. ISBN has `unique: true`. The book-author FK is encoded in a column using `referencesEntity` and `referencesColumn`, with `nullable: false`.
4. No call uses `attributes` or `relations`, or puts Mermaid in `properties`.
5. Every call includes nonempty `sources`.
