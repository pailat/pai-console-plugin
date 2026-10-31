---
name: screens
description: "Document product screens, actions, and actors in Pai Console project Knowledge (screen v3, action, actor; flows use the flows skill). Use for screen inventories, navigation maps, screen behavior and users, available actions, or connecting screens to their data."
argument-hint: "[project] [product, route, or screen to document]"
compatibility: "Pai 0.2.5+ (MCP corp; screen v3 since d65d611ac)"
---

# Screens, actions, and actors: `screen`, `action`, `actor`

Read shared `pai-console` first through the current client's skill mechanism. Branched journeys and tests use `flows`.

## Nodes

| Node | Meaning | Required fields |
|---|---|---|
| `actor` | Product user | `actorType` (`person`, `role`, `system`, `agent`), `description` (10–1000), `goals` (≥1). Optional `portalRole`, `permissions` |
| `action` | User action (button/form/link) or automatic system action. **Reusable across screens** | `trigger` (`button`, `form`, `link`, `automatic`), `effect`. Optional `inputs` (`{field, type, required}`), `outcome`, `hotspot` |
| `screen` (v3) | Route, purpose, users, states, content, actions | `route`, `purpose` (15–1500), `actors` (≥1), `states` (≥2), `content` (≥1 `{block, data?, source?}` row). Optional `actions`, `rules`, `uses`, `navigatesTo`, `prototype`, `view`/`views` |

Full templates: `../knowledge/references/kinds.md`.

### Connected v3 screens

- **`actions` are `action` node refs** (`offers`, screen → action), not `{action, effect, rule}` text rows. Literal server rejection: “Las acciones de una pantalla son nodos action: crea la acción (o corre screens:actions-to-nodes) y nómbrala por su ref.” `offers` imposes no containment: one action can appear on multiple screens.
- **`content[].source` is `{ref}`**, pointing to a block's data node (`entity`, `data_model`, `action`, `integration`, `flow`). It creates `uses` from section `content`. V2 free text remains accepted but `knowledge_audit` lists it as an unconnected source (`unconnectedSources`, literal UI “fuente sin conectar”); connect it once the node exists.
- V2 screens remain readable and migrate on their next edit or through server script `screens:actions-to-nodes`. Create actions first, then replace `actions` with refs.

Edges from `screen` refs:
- `actors` → actor `performs` screen;
- `actions` → screen `offers` action;
- `rules` → rule/constraint `constrains` screen;
- `uses` → entity/component;
- `navigatesTo` → screen (`navigates_to`);
- `content[].source {ref}` → `uses` from `content`.

For action relationships absent from its template, use `knowledge_link`:
- destination: action `navigates_to` screen;
- performer: actor `performs` action;
- data: action `uses` entity/data model (`properties.mode`: `create`, `update`, `read`);
- limitation: `business_rule`/`constraint` `constrains` action;
- trigger: action `triggers` flow/integration (payment runs Stripe).

### Screen prototypes always use a `view` block

`properties.prototype = {pageId, blockId?}` points to the Resources page drawing the screen, under the existing convention `pantallas/<product>/…`, and its **`view`** block (`pai-view@1`, `views`). Preserve existing paths; newly authored generic Resources paths follow `pai-console` naming.
- `pageId`: UUID of a page **in the same project**. Without `blockId`, use its first `view`; with it, use that block. Each `view` block represents a screen state.
- **`html` cannot be a prototype** (owner decision). HTML remains a valid resource, but cannot be linked as a screen prototype. Rebuild HTML-only screens as Pai views using `views`.
- This soft reference creates no edge and does not change the node's `pageId`. `kinds.md` omits `prototype` and action `hotspot` because they are not form fields; the server accepts them in `properties`.
- Role-based flow testing (literal UI “Probar como…”) displays the prototype with offered actions as clickable zones; without a prototype it shows the description (`flows`).
- Screen-write errors (`BAD_REQUEST` with `cause.code` and `cause.pageId`); only a new/changed prototype is checked:
  - `PROTOTYPE_PAGE_NOT_IN_PROJECT`: page absent from the screen's project, or node has no project;
  - `PROTOTYPE_BLOCK_NOT_FOUND`: page lacks that `blockId`;
  - `PROTOTYPE_NOT_VIEW`: selected block is `html`, or page has no `view`.
- **Action hotspot:** the prototype element whose visible text matches the action title. If it differs, set action `hotspot: {elementId?, text?}` (at least one), using the `view` element ID or visible text.
- Clients receive `prototype` only for a `client` page in the same project; otherwise the field is omitted.

Spanish server/UI quotations and the existing `pantallas` path convention above are intentional exceptions, not translated contract values.

## Order

1. **Search:** paginate `knowledge_library {projectId, kinds:["actor","screen","action","flow"]}` and `knowledge_search` by route/name. **Reuse** actors/actions shared with C4 and flows. If two appear equivalent, use one and flag the duplicate; never create a third.
   - For screens already drawn in Resources (view or flow blocks of pages, and whiteboards), `page_screens {organizationId, projectId}` is the project's screen index: each page's `id`, `path`, `revision`, `whiteboard` and blocks `{id, type, title, hash}`, without specs. `page_read` the page you need; a client sees only pages published to it and the flows it can see.
2. Create missing **actors**.
3. Create missing **actions** (`kn-<project>-action-<slug>`).
4. **Destination screens first.** Missing `navigatesTo` targets warn and omit the edge. Referenced `actions` and `source` nodes must also exist first.
5. **Prototype:** when a screen will be shown/tested, first create its page under `pantallas/<product>/<screen>` with a `view` block (`views`), then set `prototype: {pageId, blockId?}`.
6. Create **origin screens** with `navigatesTo`; connect `uses` to ERD entities/C4 web container and connect `content[].source`.
7. Link **action edges** through `knowledge_link` (`navigates_to`, `performs`, `uses`, `constrains`, `triggers`).
8. Create **flows** with `flows` (`flow_create` / `flow_save`). Never manually write `properties.steps`: v1 steps are now a `flow_save` projection.
9. **Verify** `performs`, `offers`, `navigates_to`, `uses` with `knowledge_get`; inspect every response's `warnings`; run `knowledge_audit` for unconnected sources.

Validated example: `examples/checkout.json`, three actions and two v3 screens with navigation and connected sources. Reuses `actor/shopper` and ERD example entities; its flow belongs to `flows`.

## Criteria

- `route`: actual English route such as `/orders/[orderId]`, not a title. Parameters use Next.js-style brackets.
- `states`: user-visible states (loading, empty, error, ready), not code states. A single-state screen may be a block within another screen.
- `content`: screen blocks with `source: {ref: "entity/<slug>"}` or their source data model/action/integration/flow.
- Name an **action** by the user's act, with `effect` and requested `inputs`; link limiting business rules through `constrains`.
- Optional `view` / `views`: inline `pai-view@1`, one per state in `views`. Flow testing renders **`prototype`**, the page's `view` block. CLI clients need text fallback and evidence before claiming a widget appeared (`pai-console` §6).

## Naming

- English kebab-case slugs: `screen/checkout`, `action/checkout-pay`, `actor/shopper`.
- Spanish business titles where required; replies follow the user's language.
- `idempotencyKey`: `kn-<project>-screen-<slug>`, `kn-<project>-action-<slug>`.

## Avoid

- Never write text rows in `actions`; create and reference action nodes.
- Never duplicate an action per screen; `offers` permits sharing.
- Never create one screen per state or minor modal; use `states`.
- Never invent routes: ask or read the repository and cite it in `sources`.
- Never put flow steps in `properties`; use `flows`.
- Never leave `actors` empty.
- Never link an `html` prototype; use `view`.
