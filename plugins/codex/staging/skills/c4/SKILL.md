---
name: c4
description: "Model a system's C4 architecture in Pai Console Knowledge using component nodes by level (context, container, component, code) and actor nodes for people, with descriptions and technology on relationships. Use for architecture, C4, context or container diagrams, components, or a system map."
argument-hint: "[project] [system or repository to document]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# C4 in Pai: `component` by level + `actor`

Read the shared `pai-console` skill first, using the current client's invocation mechanism.

## Model

- **Each C4 element is a `component` node** with `c4Level` and `c4Type`.
- **People are `actor` nodes**, never a `component` of type `Person`.
- Declare **hierarchy** with `parent`: the element at the immediately higher level contains it (`contains`).
- Declare **interactions** with `relationships`: the server creates `uses` edges between components and `performs` edges from actors.
- The diagram is generated automatically by level, with navigation across all four levels.

| `c4Level` | Allowed `c4Type` | `technology` |
|---|---|---|
| `context` | `System`, `System_Ext` | optional |
| `container` | `Container`, `ContainerDb`, `ContainerQueue`, `System_Ext` | **required** |
| `component` | `Component`, `ContainerDb`, `System_Ext` | **required** |
| `code` | `Code` (+ `codeKind`: class, interface, enum, entity, or function) | optional |

## Order

1. **Discover** the project and **search existing content**:
   - **inventory:** `knowledge_library {projectId, kinds:["component","actor"]}`, advancing `offset` to `total`;
   - **organization:** the same `knowledge_library` with `projectId: "organization"`. Shared client models and systems may live there: link their UUIDs instead of recreating them;
   - **topic:** `knowledge_search` with those kinds and the system name.
   - **by level:** `knowledge_search {query, c4Level}` (`context`, `container`, `component` or `code`) returns only `component` nodes of that level, each with `c4 {level, type, technology}`. Add `withCounts: true` for each node's `counts`: `contains` (children of a system or container, entities of a data model) and `usedBy` (incoming `uses`, such as the containers storing a data model), like Portal's Arquitectura index. Counts include only edges whose other end you can see and that are not archived.

   If the system exists, **add beneath it** rather than duplicating it.
2. **Actors first:** `actor` with `actorType` (`person`, `role`, `system`, or `agent`), `description` (10–1000), and `goals` (≥1). Reuse existing actors shared by screens and flows.
3. **Context level:** the `System` and `System_Ext` nodes (providers and client systems).
4. **Container level**, with `parent: ["component/<system>"]`. Databases use `ContainerDb`, with `dataModels: ["data_model/<slug>"]` linking to the ERD (`erd` skill).
5. **Component level** only where useful, with `parent: ["component/<container>"]` and `stereotype` where applicable.
6. **Code level:** rarely; only when requested or when the element is central.
7. **Always create the target of a relationship or `parent` first.** A missing target does not fail the write: it returns a warning and omits the edge. Resave the node once the target exists.
8. **Verify with `knowledge_view {view:"c4", scope:"component/<system>", level, format:"json"}`**, level by level (`context`, then `container`…). This is the Portal's projection.
   - Elements have their `c4Type` and `technology`; people appear as actors.
   - Relationships have the declared `description` and `technology`.
   - The `tree` attaches each element to its parent.
9. **Deliver**:
   - the diagram through `view_render` with a `C4Diagram` receiving the unmodified `knowledge_view` response (`views` skill, Knowledge diagrams); in CLI clients provide a text fallback and never claim a widget rendered without evidence;
   - `kb:` citations;
   - for a document, a `projection` block with `format: "c4"` in a v2 page (`resources` §3), a live projection rather than copied data; show an existing block with `page_projection {path, blockId}`;
   - Mermaid (`format:"mermaid"`) when requested;
   - the Portal link: the view's `url` (already includes `?level=`) prefixed by the Portal host (`https://app.pai.lat` in production; the staging Portal in staging).

**Product modules and components:** link a functional `module` to its implementation with `implemented_by` (module → component), both in the same product (`productId`). Details and errors are in `knowledge`.

Complete validated example: `examples/shop-c4.json`. It includes an actor, a system, an external system, three containers (one database linked to the ERD), a repository, and a controller.

## Relationships (`relationships`, ≤30 per node)

```json
{ "to": "component/shop-api", "direction": "out", "description": "Queries and creates orders", "technology": "HTTPS/JSON" }
```

| Field | Content |
|---|---|
| `description` | **Arrow label** (3–120 characters). A verb and object, such as “Charges orders”. **There is no `label`.** |
| `technology` | Protocol or mechanism (≤60): `HTTPS/JSON`, `SQL/TLS`, `AMQP`, `gRPC`, `Webhook`. |
| `direction: "out"` | This element uses `to`. |
| `direction: "in"` | `to` uses this element. **Always `in` for an actor**, because the person initiates the relationship. |

The `direction:to` pair is unique within a node.

Declare each relationship **once**, on its initiating node (`out`), except actor relationships, declared with `in` on the element they use.

Two elements can use each other (the API calls a provider and the provider notifies the API through a webhook): declare two relationships, one `out` on each node; the diagram shows both.

## Stereotypes (component level only)

| `stereotype` | Fields | Requires |
|---|---|---|
| `controller` | `httpRoutes[{method, path, handler?, description?}]`, `methods` | — |
| `service`, `interface` | `methods[{name, parameters?, returns?, visibility?, description?}]` | — |
| `repository` | `methods`, `dataOperations` (create, read, update, delete, list, count) | `entity: ["entity/<slug>"]`, the ERD bridge |
| `module` | `exports` | — |
| `component` | default | — |

At code level, `codeKind` determines the fields:
- `class`: `attributes`, `methods`, and `httpRoutes`;
- `interface` and `function`: `methods`;
- `enum`: required `enumValues`;
- `entity`: `attributes` and `entity`.

## Naming

- English kebab-case slugs: `shop-system`, `shop-api`, `orders-controller`.
- Spanish business titles where required; conversation replies follow the user's language.
- `technology` includes product and major version when relevant: “Next.js 16”, “PostgreSQL 16”.
- `responsibility` (15–1000 characters): what it does and excludes, in one or two sentences.

## Avoid

- Never use `c4Type: "Person"`: use an `actor`.
- Do not skip levels with `parent`: a container belongs to a context and a component to a container, otherwise `C4_LEVEL`. A node has **one** parent (`ALREADY_CONTAINED`).
- Never omit `technology` on a container or component.
- Do not write `label` or Mermaid in `properties` (`MERMAID_NOT_ALLOWED`).
- Do not use `stereotype` outside component level, or `httpRoutes` outside a controller or class.
- Do not manually create `uses`, `performs`, or `contains`: derive them from `relationships` and `parent`.
- Do not model every class: C4 explains the system rather than copying its code.

Portal Arquitectura now offers creation dialogs and editable diagram inspectors under the caller's grants. Those edits use the same Knowledge nodes, sources, complete properties, and revision checks as MCP; reread a node after someone edits it there. Diagram positions are presentation, not a substitute for the model's relationships.

## Later changes

1. `knowledge_get` the node.
2. `knowledge_update` with **all** `properties` (the complete `relationships`) and `expectedRevision`.

Removing a relationship row removes its edge. Retire an element with `knowledge_archive` and a reason.
