---
name: knowledge
description: "Create and maintain Pai Console project or product Knowledge graphs: kinds, strict templates, sources, human-confirmed proposals, CAS with expectedRevision, ontology links including implemented_by, structured knowledge_query, atomic knowledge_batch, and resolve/supersede/archive lifecycle. Use for decisions, business rules, risks, questions, assumptions, facts, glossary, modules, other nodes, or graph queries. ERD, C4, screens, flows, and API designs have dedicated skills. Also shared-node appearances in projects and edge history."
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Knowledge in Pai

Read shared `pai-console` first through the current client's skill mechanism. The graph is project memory: each node is a sourced assertion or artifact; each edge explains a relationship.

## Choose a kind

Contract-generated references: `references/kinds.md` (templates/examples), `references/ontology.md` (allowed relationships). `knowledge_kinds` returns the server's equivalent; use it when version is uncertain.

| Content | Kind |
|---|---|
| Measurable goal with a horizon | `objective` |
| Choice with context and consequences | `decision`; formal architecture choice: `adr` |
| Business requirement (“if X then Y”) | `business_rule` |
| External, non-negotiable limit | `constraint` |
| Potential failure | `risk` |
| Unknown | `question` |
| Unverified belief | `assumption` |
| Work to do | `task` (`schedule`) |
| Verifiable sourced datum / external source | `fact` / `reference` |
| Vocabulary / domain idea | `glossary_term` / `concept` |
| Functional product module | `module` |
| Screen, actor, screen action (`action`) | `screens` skill |
| Branched journey (`flow`), step service (`integration`) | `flows` skill |
| Flow test (`flow_run`) | Created only by `flow_run_start` (`flows`); `knowledge_create kind=flow_run` is rejected |
| Data model, table | `erd` skill |
| System, container, component | `c4` skill |
| OpenAPI 3.1 API design (`api`) | `api-design` skill; only `api_design_*` writes it, generic writes fail with `API_DESIGN_OWNED`. Its `uses` edges to entities and components are derived from `x-pai-entity`/`x-pai-component` on save: never link or unlink them by hand |
| Procedure / reusable approach / pitfall / approach to avoid | `runbook`, `pattern`, `gotcha`, `antipattern` |
| None of the above | `note`, as a last resort |

## Server rules for agents

1. **Required `sources`:** at least one, or `SOURCE_REQUIRED`. Types:
   - `page` `{pageId, quote?}`;
   - `page_comment` `{pageId, threadId}`;
   - `url` `{url, accessedAt}`;
   - `repo` `{path, ref?}`;
   - `chat`;
   - `meeting` `{title, date}`;
   - `ckl` `{blockId}`.

   Sources are strict: extra keys are rejected. `fact` and `reference` always require a source.
2. **Human decisions remain proposals.** Create `objective`, `decision`, `adr`, `business_rule`, and `constraint` as `proposed`. Requesting `active` yields `HUMAN_CONFIRMS`.
   - Agents cannot confirm/reject; no tool permits it. A person does so in Portal or Console.
   - Finish by **listing pending proposals** with `kb:` citations. Never describe a proposed node as active, effective or already in force, even when the user says the decision was already made: say it is recorded and awaits a person's confirmation in Portal or Console.
3. **Never edit an active node of those kinds.** Create a replacement, also `proposed`. Once a person activates it, use `knowledge_supersede`; the replacement must be `active`.
4. **People control client-visible content.**
   - Agents cannot edit, archive, or unlink client-visible nodes (`CLIENT_VISIBLE_REQUIRES_PERSON`). Never hide, edit, and republish to bypass this. Create an internal replacement proposal or ask a person.
   - In corp MCP, a **staff** agent may change visibility (`internal` ↔ `client`) using `knowledge_update` with **only** `visibility` as the content change; it records a warning. Do this last with user approval (`flows` order). Otherwise `visibility:"client"` is downgraded to `internal` with a warning.
5. **Strict templates:** `properties` must have exactly the kind's keys. Unknown keys or embedded Mermaid (`MERMAID_NOT_ALLOWED`) are rejected.
6. References accept `uuid`, `slug`, `kind/slug`, or `kb:kind/slug@rN`. Prefer **`kind/slug`** for readable, unambiguous references.

## Create

1. `knowledge_search` by topic and likely kinds. For complete kind inventory use `knowledge_library {projectId, kinds}`; for a node/topic context bundle use `knowledge_context`.
2. If equivalent content exists, **update or link it**, or propose replacement if contradictory. Never duplicate.
3. `knowledge_create` with:
   - `kind`, English kebab-case `slug`, Spanish business `title` (≤200), `summary` (≤280);
   - template `properties`, `sources`;
   - `links` (≤10 edges in the same write);
   - `changeSummary` (≤80), stable `idempotencyKey` (8–128).
4. Inspect:
   - `similar`: possible duplicates. Archive your duplicate with a reason or merge.
   - `warnings`: unresolved references, downgraded visibility.
   - The `kb:` citation to return to the user.

## Link

`knowledge_link {rel, sourceRef, targetRef, evidence}`. `evidence` (≤500) explains the edge.

| Relation | Use |
|---|---|
| `grounds` / `warrant` | Evidence/reasoning supporting a decision or rule (Toulmin) |
| `supports` / `opposes` / `rebuttal` | Support, opposition, exception |
| `depends_on`, `implements`, `refers_to` | Dependency, implementation, terminology |
| `constrains` | Rule/constraint limits a module, screen, flow… |
| `contains` | Structural hierarchy (module → screen, data_model → entity, component → component) |
| `offers` | Screen offers an action; does not impose containment, so actions can be shared |
| `triggers` | Action triggers flow/integration; flow triggers integration (a payment action runs Stripe) |
| `performs`, `navigates_to`, `uses` | Actor performs action; action navigates to screen or uses entities (`properties.mode`: create, update, read) |
| `tests` | `flow_run` tests a flow; only `flow_run_start` writes it, never manually |
| `relates_to` | ERD entity edges derived from FKs, never manually |

**`implemented_by` (module → component):** identifies a functional module's C4 implementation. Only `module` → `component`, with **both nodes in the same product** (create/link with the same `productId`). Wrong/reversed kinds → `ONTOLOGY`; project/organization node → `cause.code: IMPLEMENTED_BY_NEEDS_PRODUCT`; different products → `IMPLEMENTED_BY_ACROSS_PRODUCTS`. Moving a node with this edge out of its product yields `PRECONDITION_FAILED` `HAS_IMPLEMENTED_BY`.

**Remove an edge:** `knowledge_unlink {edgeId}` or `{rel, sourceRef, targetRef}` (staff only). It deletes only the edge, never nodes; `removed: false` means it did not exist. Removing `contains` detaches the child; removing `supersedes` restores the superseded node. Agents cannot remove client-visible edges (`CLIENT_VISIBLE_REQUIRES_PERSON`), and closed projects refuse it. Do not unlink edges the server derives (ERD `relates_to` from FK columns, flow `tests` from runs): change their source instead. Confirm before unlinking, and relink with knowledge_link if it was a mistake.

On `ONTOLOGY`, find an allowed relationship for that pair in `references/ontology.md`. Do not force a superficially similar relationship just to pass validation.

## Product Knowledge (`productId`)

`knowledge_*` (including `knowledge_view`, `knowledge_query`, `knowledge_batch`, and `task_board`) accept `productId` to work with **product Knowledge**, its current architecture/functionality, rather than project Knowledge.
- `projectId` remains required; the project must touch the product (`product_link_project`, `products`). Otherwise `BAD_REQUEST` with `cause.code: PRODUCT_NOT_IN_SCOPE`; use a project product (`product_get`).
- `knowledge_create {productId}` creates a product node, except `task`, which yields `TASK_NEEDS_PROJECT`.
- Without `productId`, `knowledge_query` already includes touched products' nodes and linked organization nodes; with it, results are product-scoped.
- Closing a project records `knowledge_merged` for every product it touched.

## Move and merge existing knowledge

Search all relevant project/product/organization scopes before duplicating content. Use knowledge_get for reference resolution and knowledge_library/knowledge_context to inspect relevant scopes; knowledge_view {view:"c4",productId} without scope renders a product context with its system, external organization systems and actors. Verify source and destination before a scope change.

- knowledge_move requires ref, toProjectId, organizationId and projectId; send expectedRevision from the current read. toProjectId:null plus toProductId targets a product, null without product targets the organization, and a project UUID targets that project. Product moves from a project must use a product it touches.
- Inspect the containment tree first with knowledge_query scope {nodeId}. HAS_CONTAINMENT means a node cannot move alone: subtree:true atomically moves the top node and its descendants. HAS_IMPLEMENTED_BY means both ends cannot remain in the same product; resolve the relationship explicitly rather than deleting it to bypass the error.
- A project-page-derived node needs releasePage:true to leave its project. Review this effect first: the page becomes provenance (grounds), and releasedPages identifies affected pages. Preserve IDs, history and comments. SLUG_TAKEN/IDENTIFIER_TAKEN return conflicts; do not rename another node automatically.
- knowledge_merge requires keepRef, duplicateRef (UUID), keepExpectedRevision, duplicateExpectedRevision and evidence (1–500), plus organizationId/projectId. Read both first and explain why they are duplicates of the same kind. Optional toProjectId/toProductId moves the survivor under the same rules.
- A merge preserves edge evidence, reports dropped duplicate edges, supersedes an assertion or archives a duplicate artifact, and never deletes it. pagesCitingDuplicate must be reviewed by a person: pages are not rewritten automatically. NEW_NOT_ACTIVE prevents an inactive survivor replacing a current node.
- Tasks cannot move or merge through these graph tools, a duplicate inside a contains hierarchy cannot merge, closed destinations reject writes, and an agent cannot move/merge client-visible content. Do not bypass these boundaries with lower-level writes.

## Structured queries: `knowledge_query`

Use for questions such as active high-priority requirements, a module's screens, or risks affecting a component:
- Required `kinds`; `status` defaults to draft, proposed, active; template `properties` `{key: [values]}`; `tags`.
- `scope {nodeId, revision}`: descendants through `contains`.
- `related {node, rels, direction: in|out|both, depth 1-3}`: neighborhood.
- `pattern {steps}` (≤4): first without `via`, subsequent steps with `via {rel, direction}`.
- `limit` ≤200; narrow results when `truncated`.

Errors: `BAD_REQUEST` with `cause.code: QUERY` and `issues` (non-template property, missing `via`, ontology-invalid edge); `TIMEOUT` `QUERY_TIMEOUT`: narrow `kinds`, `scope`, `depth`, or pattern.

## Atomic writes: `knowledge_batch`

Up to 200 atomic operations (`create` with local ref `$name`, `update`, `link`, `unlink`, `supersede`, `archive`, `resolve`, `set-status`) with batch `idempotencyKey`, `changeSummary`, `sources`, and optional `productId`.
- **Always inspect response `status`.** Rejection **is not an MCP error**: `status: "rejected"`, and each failed operation's `results[i].error {code, message, allowedTargets?, suggestedRels?, currentRevision?}`. Nothing was written; preceding `ok: true` operations were rolled back.
- **People decide `set-status`:** MCP callers are agents, so a batch containing it is `rejected` with `HUMAN_CONFIRMS` (ATE-184). Remove it and keep nodes `proposed`.
- Rejected keys are not consumed: correct and retry with the same key. Reusing a consumed key with different input yields `IDEMPOTENCY_MISMATCH`; identical input yields `replayed: true`.

## Update with CAS

1. `knowledge_get`: current `revision`, complete `properties`.
2. Modify **that copy**.
3. `knowledge_update {ref, expectedRevision, changeSummary, …}`. Supplying `properties` **replaces them completely**; omitted fields are deleted. Omit `properties` when changing only `status`, `title`, `summary`, `tags`, or `sources`.
4. On `CONFLICT` (`REVISION`), reread, integrate, retry once.

## Lifecycle

| Situation | Tool |
|---|---|
| Answered `question` or confirmed/refuted `assumption` | `knowledge_resolve` with `outcome` (`answered`, `confirmed`, `refuted`), `evidence`, `idempotencyKey`, and either inline `resolution` draft **or** `resolutionRef`, never both; links with `supports` or `opposes` |
| Mitigated `risk` or completed `task` | `knowledge_resolve` with `outcome` `done` or `wont_do` |
| Replacement | `knowledge_supersede {oldRef, newRef, evidence}`; replacement must be `active` |
| No longer applicable | `knowledge_archive {reason}`, reversible with `knowledge_revive`; nodes are not deleted |
| Read and useful | `knowledge_observe` (inexpensive, not audited) |

## Graph health

- `knowledge_audit`: weak/thin (unjustified) nodes, orphans, unresolved questions, and unconnected screen sources (`unconnectedSources`: `content.source` text instead of `{ref}`, `screens`). Run at the end of a modeling session and report results.
- `knowledge_impact` (`maxDepth` ≤3): affected nodes if one changes. Use before proposing a decision replacement.
- `knowledge_graph {projectId?}`: nodes/degrees, edges, hubs (`hubThreshold`), for project or organization central nodes and orphans.
- **Organization Knowledge:** nodes can have no project (shared glossary, client rules, systems).
  - `knowledge_library` and `knowledge_graph` accept a project (its nodes plus linked organization nodes), `"organization"` (organization nodes only), or omitted `projectId` (everything).
  - These nodes return `project: null`.
  - **Also search `"organization"` before project creation.** Link existing content (`knowledge_link` accepts UUID `targetRef`) rather than duplicating it.
  - Use knowledge_move for supported project/product/organization movement under the current IAM grants; direct creation still follows knowledge_create scope. Read the movement workflow above before changing scope.
  - Organization node Portal path: `/organization/knowledge/<nodeId>`.
- **Show a shared node in a project without moving it:** `knowledge_appearance_set {organizationId, projectId, ref, productId?}` makes a product or organization node appear in that project, keeping its scope, parent and visibility. The project must be open and touch the node's product. Tasks cannot appear (`TASK_NEEDS_PROJECT`) and a project node already lives in a project (`PROJECT_NODE_APPEARANCE`). `knowledge_appearance_remove` stops showing it. Both are idempotent (`changed: false` on repeat) and need `knowledge.nodes.update` on both scopes; prefer an appearance over a duplicate or a move when several projects need the same node, and confirm first because it changes what that project's readers see.
- **Edge history:** `knowledge_edge_history {organizationId, projectId, ref, productId?, limit?, cursor?}` lists a node's relationship changes with actor, change, evidence and canonical scopes before/after. Cursors and revisions are decimal strings: pass them back unchanged and follow `nextCursor` for older entries. It is a staff read, not a changefeed, and is not available inside a Pai Agent session. Use it to explain when and why an edge appeared or disappeared.
- Legacy Knowledge task nodes/projections stay project-scoped. Unified tasks also support product backlogs and CRM contexts through `../tasks/SKILL.md`; do not create those with knowledge_create.

## Client visibility (ATE-237)

Clients have **read-only Knowledge** in Portal and MCP:
- Only `visibility: "client"` nodes, and edges with **both endpoints** visible.
- Project reads: `knowledge_kinds`, `knowledge_search`, `knowledge_get`, `knowledge_impact`, `knowledge_view`.
- No writes (`knowledge_create`, `update`, `link`, `batch`…), `knowledge_context`, `knowledge_audit`, `knowledge_query`, or organization Knowledge (`knowledge_library`, `knowledge_graph`). `task_board` remains staff-only.
- Only `client` flows; internal-node references are labeled with the server's literal “Interno” (`flows`).

Consider publication effects: a `client` node with an `internal` neighbor appears without that edge. Write client-visible `title`, `summary`, and `properties` for the client: no staff emails, IDs, or internal notes. Server/UI labels quoted in Spanish are intentional literal exceptions.

## Avoid

- Never invent sources or create unsourced nodes. If the conversation is the source, use `{type:"chat"}` and say so.
- Never retry `HUMAN_CONFIRMS` repeatedly: it is a boundary.
- Do not use `note` when a dedicated kind applies.
- Do not bury another node in `properties`: a decision in risk notes should be a linked `decision`.
