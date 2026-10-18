---
type: llm
focus: mock_calls
---

PASS only if the `knowledge_create` calls satisfy every condition:
1. The shipment has two distinct foreign-key columns to the same warehouse entity, named by role (for example `origin_warehouse_id` and `destination_warehouse_id`, never `warehouse_id_2`), both with `nullable: false`.
2. No intermediate table or combined origin/destination column is used to avoid parallel FKs.
3. The zone has a self-reference to its own slug with `nullable: true`.
4. The warehouse has its zone FK in a column using `referencesEntity` and `referencesColumn`.
5. No call uses `attributes`, `relations`, or Mermaid in `properties`, and every call includes nonempty `sources`.
