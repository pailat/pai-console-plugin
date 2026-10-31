---
name: erd
description: "Model an ERD in Pai Console project Knowledge with data_model and entity nodes, typed columns, and relationships derived from foreign keys. Use for data models, ERDs, tables, entities, database schemas, or importing schema.sql or migrations into Pai."
argument-hint: "[project] [domain description | schema.sql or migrations path]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# ERD in Pai: `data_model` + `entity`

Read `pai-console` first (environment, discovery, search before create, CAS), using the current client's skill invocation mechanism.

## Model

A **`data_model`** groups **`entity`** nodes (tables). **An entity is its columns.** Never write relationships directly: foreign-key columns define them. The server derives cardinality, creates `relates_to` edges, and generates the diagram.

## Order

1. **Discover** organization and project (`pai-console` §1).
2. **Search existing content:**
   - **inventory:** `knowledge_library {projectId, kinds:["data_model","entity"]}`, advancing `offset` to `total`;
   - **organization:** the same call with `projectId: "organization"`. Shared client models and systems may live there: link their UUIDs instead of recreating them;
   - **topic:** `knowledge_search` with those kinds and domain terms in Spanish and English.

   If a model exists, **extend it** with entities pointing to it through `dataModel`. Do not create another.
3. **Establish the source.** An agent must cite the model's origin (`SOURCE_REQUIRED`):
   - `{type:"repo", path:"db/schema.sql", ref:"main"}`;
   - a Resources page (`{type:"page", pageId}`);
   - a meeting (`{type:"meeting", title, date}`).
4. **Create the `data_model`.** Required `purpose` (15–1500 characters); optional `engine`, `namespace` (snake_case), and `conventions`.
5. **Create entities in dependency order:** referenced entities before referencing entities.
   - An FK targeting a missing entity **does not fail**: it returns a warning and omits the edge.
   - Resave the entity (`knowledge_get` → `knowledge_update` with the same `properties` and `expectedRevision`) once the target exists.
6. **Inspect every `knowledge_create` response:**
   - `warnings`: unresolved FK, downgraded `visibility`;
   - `similar`: possible duplicate. If equivalent, stop and merge.
7. **Verify with `knowledge_view {view:"erd", scope:"data_model/<slug>", format:"json"}`**, the Portal's projection.
   - `tables`: all entities and columns.
   - `relations`: **one per FK column**, including multiple FKs to one table, with expected `cardinality` (`n-1` or `1-1`), `identifying`, `optional`, and `onDelete`. Count `referencesEntity` columns: the relation count must match.
   - **Empty `unresolved`.** Otherwise an FK target is missing or is not an `entity`; correct and resave.
8. **Deliver**:
   - `view_render` with an `ErdDiagram` receiving the unmodified `knowledge_view` response (`views`, Knowledge diagrams); provide a CLI text fallback and never claim a widget rendered without evidence;
   - each node's `kb:` citation;
   - for a document, a live `projection` block with `format: "erd"` in a v2 page (`resources` §3), rather than copied data; show an existing block with `page_projection {path, blockId}`;
   - the view's Mermaid (`format:"mermaid"`) when requested;
   - the Portal link: the view's `url` prefixed by the Portal host (`https://app.pai.lat` in production; the staging Portal in staging).

Complete validated example (model, 5 entities, simple FK, two FKs to one table, identifying FK, self-reference, and enum): `examples/sales-erd.json`.

## Columns: exact contract

Each `columns` row (1–80; at least one `primaryKey`):

| Field | Rule |
|---|---|
| `name` | `^[a-z][a-z0-9_]*$`, ≤63 characters, English snake_case, unique within the entity |
| `type` | `uuid`, `text`, `integer`, `bigint`, `numeric`, `real`, `boolean`, `date`, `time`, `timestamptz`, `interval`, `jsonb`, `bytea`, `vector`, or `enum` |
| `nullable`, `primaryKey`, `unique` | **Required** booleans, no defaults. A PK cannot be `nullable` |
| `referencesEntity` + `referencesColumn` | Both present or both absent. The first is `entity/<slug>` |
| `onDelete` | `no_action`, `restrict`, `cascade`, or `set_null`. FK only; `set_null` requires `nullable: true` |
| `enumValues` | Only with `type: "enum"`, then required (≤50) |
| `isArray`, `default` (≤120), `description` (≤300) | Optional |

Other entity properties:
- `physicalName`: table name, snake_case.
- `dataModel`: `["data_model/<slug>"]`, at most 1.
- `purpose`: required, 15–1500 characters.
- Optional `invariants` list, `lifecycle`, and `notes`.

### SQL translation

| SQL | Pai |
|---|---|
| `varchar(n)`, `char`, `citext` | `text` (record length in `description` if relevant) |
| `int`, `smallint`, `serial` | `integer`; `bigserial` becomes `bigint` |
| `decimal(p,s)` | `numeric` |
| `float8`, `double precision` | `real` |
| `timestamp` (without zone) | `timestamptz`, explaining the distinction in `description` |
| `json` | `jsonb` |
| `CREATE TYPE … AS ENUM` | `type:"enum"` + `enumValues` |
| `text[]` | `type:"text"`, `isArray:true` |

## Derived cardinality

| FK column | Result |
|---|---|
| Normal | `n-1` (many rows reference one) |
| `unique: true`, or the entire PK | `1-1` |
| Part of the PK | **Identifying** relationship |
| `nullable: true` | Optional relationship |
| Many-to-many | **Join table** with two FKs in the PK (like `order_line` in the example) |
| Own table (`parent_id → id`) | Self-referencing `n-1`; use `nullable: true` (the root has no parent) |

There is no direct `n-m`.

### Multiple FKs to one table and self-references

These are normal modeling patterns; the diagram shows all of them:
- **Multiple FKs to one table:** each column has its own relationship, line, and cardinality. Examples: `billing_address_id` and `shipping_address_id` → `address`, or `node_id`, `conflicting_node_id`, and `resolution_node_id` → `knowledge_node`. Do not combine them or add an intermediate table to avoid them.
- **Name each FK by role** (`billing_address_id`, not `address_id_2`), explaining it in `description`: the diagram distinguishes lines by column name.
- **Self-reference** (tree: `category.parent_id → category.id`): `nullable: true` with `onDelete: "set_null"` or `"cascade"` depending on whether children survive the parent. It appears in the ERD and `knowledge_view` relations, but creates no `relates_to` edge (the graph forbids edges from a node to itself).

## Naming

- English kebab-case slugs: `data_model/sales-model`, `entity/order-line`.
- Columns and `physicalName`: snake_case.
- Spanish business titles where required; conversation replies follow the user's language.
- Always send an explicit `slug`: references such as `entity/customer` depend on it.
- `idempotencyKey`: `kn-<project>-entity-<slug>`.

## Avoid

- Never write `attributes`, `relations` (v1 format), or other unknown keys: the strict template rejects them.
- Never create `relates_to` edges or cardinalities manually; derive them from FKs.
- Never write Mermaid in `properties` (`MERMAID_NOT_ALLOWED`); the diagram is generated.
- Do not use types outside the vocabulary (`varchar`, `string`, `int4`…) or camelCase names.
- Do not point `referencesEntity` at a non-`entity`: it warns and omits the edge.
- Do not request `visibility:"client"`: an agent only writes `internal`; a person decides publication in Console.

Portal Arquitectura now offers creation dialogs and editable diagram inspectors under the caller's grants. Those edits use the same Knowledge nodes, sources, complete properties, and revision checks as MCP; reread a node after someone edits it there. Diagram positions are presentation, not a substitute for the model's relationships.

## Later changes

1. `knowledge_get` the entity for `revision` and complete `properties`.
2. Modify the complete `columns` list.
3. `knowledge_update` with all `properties` and `expectedRevision`. An omitted column **is deleted**.

Retire an entity with `knowledge_archive` and a reason, rather than deleting it. Changing an FK target recalculates its edges.
