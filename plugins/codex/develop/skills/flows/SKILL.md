---
name: flows
description: "Pai Console project flows (ATE-230): entity-backed steps, labeled branches, actor/screen/action/integration refs, and role-based tests. Covers flow_list/get/create/save with CAS and graph or Mermaid, version bumps, flow_run_* tests, simulated integrations with sampleResponse/sampleCases, test readiness, and client publication order. Use to create, correct, simulate, test, or prepare a branched journey or process for clients."
argument-hint: "[project] [flow to create, correct, or test]"
compatibility: "Pai 0.2.5+ (MCP corp; flow_* in develop since d65d611ac)"
---

# Flows: `flow_*` and `flow_run_*`

Read shared `pai-console` first through the current client's skill mechanism. `screens` covers `actor`, `screen`, and `action`; `knowledge` covers the remaining graph.

A flow **describes, displays, and tests** a journey:
- It is both a Knowledge `flow` node and an entity with `flow_step` rows and `flow_transition` branches.
- In Portal it lives at `/{org}/{project}/flows`, with canvas, role-based testing, Tests/Versions tabs, and next-iteration `notes`.
- Node `properties.steps` and `alternatives` are **projections** written by `flow_save`. `knowledge_update` rejects changes with the literal server message “Los pasos de este flujo se editan en el canvas o con flow_save, no con knowledge_update.”

## 1. Model

**Step** (`steps[]`): `{key, kind, title, detail?, actor?, screen?, action?, integration?, position?}`.

| `kind` | Meaning |
|---|---|
| `start` | Flow trigger (from `trigger`) |
| `step` | User/system action |
| `decision` | Branch point; **never has `screen`** |
| `end` | Outcome (from `outcome` or each ending branch) |

- Stable `key` within the flow (`[A-Za-z0-9_-]`, ≤64). Omitted steps **are deleted**.
- `actor`, `screen`, `action`, `integration`: correct-kind refs (`kind/slug`, UUID, short ID) from **project or organization**. Missing/wrong kind yields `invalid_input`, `cause.code: FLOW_STEP_REF`, and path such as `steps.3.screen`.
- `detail`: expected result shown to the tester.

**Transition** (`transitions[]`): `{from, to, kind, label?}`.
- `next` (default): main path.
- `branch`: labeled decision outcome.
- `alternative`: labeled deviation.
- `branch` and `alternative` require `label`; no self-transitions or duplicates.

Limits: 120 steps, 240 transitions. **Default** `layoutDirection: TB`; send `LR` only if requested.

**Referenced nodes** (`knowledge_create`, `knowledge`; templates `../knowledge/references/kinds.md`):

| Kind | Purpose | Required |
|---|---|---|
| `actor` | Step performer | See `screens` |
| `screen` | Step location (v3) | See `screens` |
| `action` | User or automatic system action | `trigger` (`button`, `form`, `link`, `automatic`), `effect` |
| `integration` | Step service (Stripe, webhook, IdP) | `provider`, `state` (`described`, `simulated`, `real`), `operation`; `simulated` requires `sampleResponse` (JSON ≤16 KB); `sampleCases` (`{case, response}`) adds selectable test cases |

`flow_save` derives edges from steps (`fromSection: "flow_steps"`): actor `performs` flow, flow `uses` screen/action, flow `triggers` integration. Manually link an initiating action with `knowledge_link` action `triggers` flow.

## 2. Tools

| Tool | Behavior | Access |
|---|---|---|
| `flow_list` | Project refs, titles, versions, steps, roles, latest test | Staff/client (only `client` flows) |
| `flow_get {ref}` | Trigger, outcome, ordered referenced steps, transitions, `revision`, version, latest tests and step results; `Flow` view on MCP Apps hosts | Staff/client |
| `flow_create {title, trigger?, outcome?, summary?, visibility?, graph?, sources, idempotencyKey?}` | Creates flow; without `graph`, creates trigger start and outcome end; requires `sources` | Staff |
| `flow_save {ref, graph \| mermaid, expectedRevision, idempotencyKey, changeSummary?}` | **Replaces** complete graph | Staff |
| `flow_version_bump {ref, label}` | v1 → v2… with label; does not change `revision` | Staff |
| `flow_run_start {ref, actor?, mode}` | Starts test, returns its `ref` | Staff/client |
| `flow_run_step {run, stepKey, result, note?, branchLabel?, integrationResponse?}` | Records step | Test initiator |
| `flow_run_finish {run, status, stoppedAtKey?, notes?}` | Closes test | Test initiator |
| `flow_run_list {ref, limit?}` / `flow_run_get {run}` | History/details | Staff/client; clients see their organization's tests, not Pai team's |

All receive `organizationId` and `projectId`. Flow `ref`: UUID, short ID, `flow/<slug>`, or slug.

### `flow_save`: CAS and idempotency

1. `flow_get` for `revision`.
2. Compose the **complete** graph from that read; omitted content is deleted.
3. `flow_save` with that `expectedRevision` and stable `idempotencyKey` (`flow-<project>-<slug>-<n>`). Reuse on retry.
4. On `CONFLICT`, another user saved first (live collaborative canvas). Reread, integrate, retry once.
5. Inspect `warnings` and the returned flow/new `revision`.

**Mermaid** instead of `graph`: `{…}` decision, `([…])` start/end, `-->|condition|` from a decision creates a branch, `-. text .->` an alternative. Suitable for drafts; actor/screen/action/integration refs require `graph`.

## 3. Reuse before creating

The Unicef project previously received duplicate actors/actions. Prevent recurrence:

1. `flow_list` and paginated `knowledge_library {projectId, kinds: ["flow","actor","screen","action","integration"]}` (`offset` to `total`). Search organization nodes too: flows can reference its actors.
2. `knowledge_search` by name in Spanish and English.
3. **Migrated flows:** v1 property-based flows already have entities (`flows:backfill`) or acquire them on opening. **Correct with `flow_save`; never create replacements merely for migration.**
4. If two nodes seem equivalent, use one and flag the duplicate for a person; never create a third.

## 4. Test readiness

Role-based testing (literal UI “Probar como…”) begins at `start` and follows transitions. Verify with `flow_get` before declaring completion:

- [ ] **Exactly one `start`**; without it the start control is disabled (blocked 24 migrated develop flows).
- [ ] **At least one `end`**; every path ends in one.
- [ ] **Every step reachable** from start.
- [ ] **Each decision has ≥2 labeled branches**. Explicit alternatives only in prose/`notes` must become branches.
- [ ] **Actor on every step**, including decisions/ends, for role selection and dimming other roles.
- [ ] **Link existing screen/action**; never screen on decision. A testable screen needs `prototype: {pageId, blockId?}` pointing to its page under `pantallas/<product>/…` with a **`view`** block. `html` is not a screen prototype (`screens`).
- [ ] **Link integrations.** For testing, use `state: simulated`, `sampleResponse`, and variant `sampleCases` (success, refund, dispute…).
- [ ] `detail` on each step: tester's expected result.

`../../tools/validate-examples.ts` applies this checklist to `flow_save` examples.

**Never invent business rules.** Unspecified decision owners, branches, or integration responses belong in flow `notes` (next iteration) or a `question` (`knowledge`); report them. Unresolved develop examples include a missing validator-role node, a step mixing three roles, and contradictory ends.

## 5. Test with `flow_run_*`

1. `flow_run_start {ref, actor: "actor/<role>", mode}`.
   - `sample` uses example data; `simulated` uses integration samples. `real` remains disabled (`FLOW_RUN_REAL_DISABLED`).
   - `actor` must be a flow actor (`FLOW_RUN_ACTOR` otherwise). Archived/superseded flows cannot run (`FLOW_RUN_FLOW_CLOSED`).
2. Traverse from `start`, recording each `flow_run_step`. A linked screen displays its prototype `view` and offered action hotspots in Portal testing; without prototype, only description:
   - `passed`: meets `detail`;
   - `noted`: passes with observation; use when **integration or screen is missing** and review relied only on description, explaining in `note`;
   - `failed`: expectation unmet, test stops;
   - `skipped`: another role or inapplicable branch;
   - decision `branchLabel` must match the chosen label; simulated step `integrationResponse` records the response/case shown.
3. `flow_run_finish`: `passed`, `passed_with_notes` (if any `noted`), `failed` (with `stoppedAtKey`, or inferred last failed step; neither yields `FLOW_RUN_STOPPED_AT`), or `abandoned`.
4. Cover important branches with **one test per branch** (happy path and each end), rather than mixing them into one.

Only the initiator continues a run (`FLOW_RUN_NOT_RUNNER`); closed runs cannot change (`FLOW_RUN_FINISHED`); missing step key gives `FLOW_RUN_STEP_KEY`. Tests create `flow_run` nodes with `tests`; never `knowledge_create kind=flow_run`.

## 6. Client publication order

Agents cannot edit client-visible nodes (`CLIENT_VISIBLE_REQUIRES_PERSON`). Corp staff agents may change visibility alone and save a `client` flow graph through `flow_save`.

1. Create **everything `internal`**: actors, screens, actions, integrations, flow.
2. Build with `flow_save`, check §4, test §5.
3. **Last**, with user approval, reread each node via `knowledge_get`, then `knowledge_update {ref, expectedRevision, visibility: "client", changeSummary}`. Visibility only, no other content changes.
4. Later client-node corrections require a proposal or person. Never hide, edit, and republish to bypass the boundary.

Clients see only `client` flows. Invisible refs are returned as literal “Interno”, without ref; `sampleResponse` is shown only for `client` integrations. Spanish literal UI/server strings and existing paths above are intentional exceptions.

## 7. Display

- Conversation: `flow_get` can render on MCP Apps hosts; otherwise try `view_render` with `Flow` (`views`). **CLI requires text fallback**, and no rendering claim without evidence (`pai-console` §6).
- Page: `{id, type: "flow", node, title?, height?}`, with same-project flow **UUID** in `node`, renders a read-only canvas and open control (`resources`).

## 8. Examples

Validated against contracts and develop `flow_get` on 2026-10-15: steps, refs, `next` transitions, branches, and text matched; no `layoutDirection` (TB). `flow_save` examples reproduce existing graphs (Unicef r6, Morelos r2), so saving the original graph does not change it; use it as the correction baseline. Preserve authentic captured labels when editing existing graphs; translated synthetic examples are not proof of current server text.

- `examples/unicef-donation.json`: donation payment to Unicef (`flow/donation-payment`, Checkout Merchants). Search, `flow_get`, `flow_save` with 22 steps and branches for recipient eligibility, approval/rejection, no changes, partial refund, dispute won/lost, a `simulated` customer test with Stripe, then `client` visibility.
- `examples/morelos-entry.json`: entry journey (`flow/flow-pf-entry`, Portal Funcionario), IdP authentication and membership-count decisions (none/one/many); `sample` test marks the Llave Morelos step `noted` because its integration is absent.

Synthetic graph excerpt, preserving identifiers:

```json
{
  "steps": [
    {"key": "start", "kind": "start", "title": "Customer chooses a donation and selects Pay", "actor": "actor/customer"},
    {"key": "c1", "kind": "decision", "title": "Does the bank approve the card?", "actor": "actor/customer"},
    {"key": "s6", "kind": "step", "title": "Charges and transfers the donation to Unicef", "actor": "actor/stripe",
     "integration": "integration/stripe-payment-intent-transfer-data"},
    {"key": "c2", "kind": "end", "title": "Card declined", "actor": "actor/customer"}
  ],
  "transitions": [
    {"from": "c1", "to": "s6", "kind": "branch", "label": "Approved"},
    {"from": "c1", "to": "c2", "kind": "branch", "label": "Declined"}
  ]
}
```

## Avoid

- Never write flow steps through `knowledge_create`/`knowledge_update` `properties.steps`; use `flow_save`.
- Never send a partial graph: omitted steps are deleted.
- Never leave clearly specified alternatives only in `notes`; model branches.
- Never invent actors, decisions, or integration responses to pass readiness checks; record uncertainty.
- Never publish `client` before finishing and testing the graph.

## Preserve canvas and screen state

`flow_create` and `flow_save` accept `graph.viewport {x,y,zoom}` (zoom >0) and step `position {x,y}`. Preserve these from a complete flow_get when editing an existing graph. `screenState` selects a linked screen prototype state by its actual key or name; read screen.prototype.states from flow_get, never invent a state. Keep layoutDirection TB by default or the existing value; use LR when requested. These are graph fields, not top-level tool keys. Full graph replacement still deletes omitted steps/transitions and requires fresh CAS and stable idempotencyKey.
