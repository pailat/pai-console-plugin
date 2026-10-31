# Release 0.2.5 synchronization — ATE-405

This audit covers every first-parent merge in pai-portal `a6fd71519..dbe7832cb`, the observed `origin/release/0.2.5` tip on 2026-10-30 (America/Mexico_City). The source checkout was read-only. Plugin branch `docs/0.2.5-release-sync` starts with plugin #14 and incorporates #15; its replacement PR targets `main`. No tag, plugin release, or merge is part of this task.

The source of truth is each merge's diff against its first parent, including `packages/contracts/src/mcp-tools.ts`, the actual MCP registrations and input schemas, `scripts/iam/catalog.json`, and affected domain, API and UI code. A permission in the catalog is not evidence of a callable tool. Internal methods and UI navigation changes are distinguished from public MCP contracts below.

## Complete merge audit

| pai-portal PR | Released behavior | Plugin change and reason |
|---|---|---|
| [#423](https://github.com/pailat/pai-portal/pull/423) | Position migration test timeout only | No workflow change; tests do not change tools, inputs, permissions or user behavior. |
| [#419](https://github.com/pailat/pai-portal/pull/419) | Visible test-ID helper for product E2E fixtures | No workflow change; test selection only. |
| [#412](https://github.com/pailat/pai-portal/pull/412) | Audit cleanup removes unused exports/comments and consolidates shared presentation/BFF helpers | Regenerated references and literal inventory. Reviewed removed exports: registered tool names, schemas, permission checks and actionable domain behavior remain intact; do not teach removed internal helpers as tools. |
| [#427](https://github.com/pailat/pai-portal/pull/427) | New-proposal action moves into the content toolbar in Console and Portal, with matching loading state | `proposals-payments` locates the action above the list; drafting, sending and client-response rules remain authoritative. |
| [#424](https://github.com/pailat/pai-portal/pull/424) | Live resource refresh avoids interrupting active editing | No MCP workflow change; no new save or event input. |
| [#355](https://github.com/pailat/pai-portal/pull/355) | Flow version history uses the shared list table | No workflow change; existing `flow_*` version and CAS guidance still applies. |
| [#422](https://github.com/pailat/pai-portal/pull/422) | Slug resolution can include project detail to avoid a duplicate server read | Audit records the HTTP optimization; no new MCP tool or argument. Later PF-1 controls which details may be included. |
| [#428](https://github.com/pailat/pai-portal/pull/428) | Re-exports proposal section count for skeleton rendering | No contract or permission change; toolbar location is documented with #427. |
| [#401](https://github.com/pailat/pai-portal/pull/401) | Portal Architecture creation dialogs and editable C4/ERD inspectors use existing Knowledge mutations | `c4` and `erd` explain Portal editing and rereading after edits, preserving complete properties, sources and CAS. No invented architecture-write tool. |
| [#421](https://github.com/pailat/pai-portal/pull/421) | Organization Resources navigation and entry guard use `resources.folders.list` on the organization | `resources` and `iam` distinguish organization library entry from project-only grants; no role-name shortcut. |
| [#429](https://github.com/pailat/pai-portal/pull/429) | Search embedding circuit-breaker test only | No workflow change; no public contract changed. |
| [#378](https://github.com/pailat/pai-portal/pull/378) | Knowledge library table, graph controls and loading consistency | Regenerated Knowledge references; no new Knowledge schema or permission. Existing library pagination/inventory guidance remains valid. |
| [#356](https://github.com/pailat/pai-portal/pull/356) | Appearance theme history list and mobile layout | No MCP workflow change; existing theme history/revert and approval rules still apply. |
| [#425](https://github.com/pailat/pai-portal/pull/425) | Serial IAM ancestor evaluation and consolidated resource reads; identity client handles HTTP 429 as `RATE_LIMITED` | Audit records implementation/performance and sign-in error handling; no new MCP retry or permission bypass. Existing effective-grant diagnosis remains valid. |
| [#363](https://github.com/pailat/pai-portal/pull/363) | IAM members/groups/roles/policies/Pai-access lists and settings navigation use shared list presentation | No new access mutation; `iam` continues to use exact permission catalog, policies, etags and grants. |
| [#417](https://github.com/pailat/pai-portal/pull/417) | Shared list-table labels/search behavior and updated E2E selectors | No MCP workflow change; do not turn UI filter labels into new tool fields. |
| [#346](https://github.com/pailat/pai-portal/pull/346) | Console chat adopts shared Markdown rendering and local-link handling | No tool input or authorization change; existing chat output remains data. |
| [#431](https://github.com/pailat/pai-portal/pull/431) | Product link copy actions and project navigation labels | `products` explains returned repository/deployment links and project-label navigation without implying access. |
| [#434](https://github.com/pailat/pai-portal/pull/434) | Deletes milestone Stripe checkout endpoint/action, use case, obsolete payment contract and `payments.milestoneCheckouts.create`; cleans retired grants, denies and custom boundaries | `schedule`, `proposals-payments` and `iam` explicitly route collections through CFDI/payments and forbid recreating the removed checkout permission. No `payment_*` MCP tool was removed. |
| [#430](https://github.com/pailat/pai-portal/pull/430) | Mobile impersonation banner layout | No MCP change; identity restoration behavior is documented with #435. |
| [#433](https://github.com/pailat/pai-portal/pull/433) | Resource document/note/whiteboard headers, inline properties and actions | `resources` explains the current action/property location, preserving existing property tools, authorization and read/write rules. |
| [#432](https://github.com/pailat/pai-portal/pull/432) | Removes the legacy Console block editor in favor of collaborative editor and reader fallback | `resources` stops directing users to a legacy editor. No new MCP save operation. |
| [#436](https://github.com/pailat/pai-portal/pull/436) | Nonblocking structural warnings from full page reads, validation and writes | Incorporated plugin #15. `resources` documents `TEXT_OVERFLOW`, `ORPHAN_GRID_ITEM`, `GRID_COLUMNS_OVERFLOW`, approximate reference measures and suggestions; regenerated literal page tool descriptions. No claim of browser rendering. |
| [#435](https://github.com/pailat/pai-portal/pull/435) | Stale anonymous requests after stopping impersonation no longer erase restored root-session cookies | `pai-console` instructs refreshing/verifying identity before another action; backup cookies confer no authorization. No membership workaround. |
| [#437](https://github.com/pailat/pai-portal/pull/437) | Native host registry, identity checks, revision/state transitions, fenced internal incarnations, organization IAM roles | `organizations` and `iam` document public identity, pending status, permanent revocation and runtime boundaries; internal runtime methods are not public tools. |
| [#396](https://github.com/pailat/pai-portal/pull/396) | PF-1 Resources-only project access through folder/page grants, separate shared project entries and reader-relative paths across HTTP/MCP | `pai-console`, `resources` and `iam` document `full`/`resources`, hidden ancestors, per-resource checks, shared pagination and absent shared entries in agent-scoped reads. Never infer whole-project access from a resource grant. |
| [#438](https://github.com/pailat/pai-portal/pull/438) | Console milestone tasks use searchable paginated list, permission-gated task links and dependency row menu | `schedule` and `tasks` document task opening under `tasks.tasks.get` separately from dependency controls; no new task status or primitive. |
| [#440](https://github.com/pailat/pai-portal/pull/440) | Five corp staff-only connection tools, strict schemas, HTTP/Console Conexiones screens and per-organization grants | Regenerated inventory adds `connection_list/get/events/create/revoke`. `organizations` teaches exact inputs/pagination, public-only identities, create replay/conflict and revision-safe permanent revoke. `pai-console` routes discovery; Claude explorer adds only the three reads; shared policy requires list-before-create and describes irreversible revoke. Codex packages regenerated from sources. |
| [#439](https://github.com/pailat/pai-portal/pull/439) | Direct resource resolution authorizes the target without enumerating its parent; folder entry hints respect readable content | `resources` documents direct links independent of denied parent listings and visibility-filtered `hasEntries`. No invented MCP resolver tool; returned paths remain reader-relative. |

## Reproducible generation

A `git archive dbe7832cb` of pai-portal was copied into `/portal` in disposable Railway sandbox `bce67bb8-330d-40ab-8427-86dd295e11e4` (Pai project, develop environment). Dependencies were installed there with `bun install --frozen-lockfile --ignore-scripts`. The plugin archive ran:

```bash
PAI_PORTAL=/portal bun tools/gen-references.ts --source-revision dbe7832cb
python3 tools/build_codex.py
```

Only source-generated references, `hooks/tools.json`, and the compact literal `evals/mocks/pai/_tools.json` were copied back; shared skills and client adapters were edited in their maintained source locations and packages rebuilt. No generated package was hand-edited. Generation returns **313 corp tools: 127 reads and 186 writes**; upstream declares 315 names, including the two client-only `proposal_accept` and `proposal_reject`. The five new tool names account for the difference from the previous 308-tool plugin snapshot. Existing `iam_access_test`, `iam_access_explain`, `iam_boundary_set`, `iam_role_create` and `iam_role_update` input schemas refresh permission enums; `page_read` and `page_validate` refresh structural-warning descriptions. No existing tool was removed. Literal Spanish server descriptions remain intentional source-owned contract data; maintained prose is English.

## Validation

The full gate passed on `c5a5224` in the same disposable Railway sandbox; only this evidence record was added afterward. Log: `~/worktrees/reui-orch/logs/sandbox/plugin-sync-gate-final.log`.

- `PAI_RUN_CODEX_RUNTIME=1 make check`: **112 tests passed**, no skips; generated Codex packages are byte-reproducible and the English authoring check reported zero findings.
- `PAI_PORTAL=/portal bun tools/validate-examples.ts`: **19 files, zero failures**, against actual archived upstream contracts.
- `claude plugin validate --strict` for `.`, `.claude-plugin/plugin.json`, `skills`, and `agents`: all four passed with Claude Code **2.1.289**.
- Native Codex installation/switch tests passed on **codex-cli 0.160.1** in isolated temporary homes. The opt-in native approval fixture executed `whoami` and `page_read`, rejected prompts for `page_update` and unknown `future_write`, and received **zero writes**. This tests installed native policy against local fixtures, not deployed hook trust.
- Repeated full `gen-references.ts --source-revision dbe7832cb` preserved every reference and both inventory files byte for byte (`sha256sum -c`); a subsequent `build_codex.py --check` passed.
- Local read-only QA compared the audit table to the exact merge list: **29/29 PRs**, no omissions or extras. `git ls-remote` confirmed the remote release remained at `dbe7832cbe4e3421ca2c895cb71a0061cd41a002`. The final diff passed `git diff --check`.

The first gate on `cd1e377` exposed a new guard test missing its empty transcript fixture and a README checkpoint/count mismatch; both were corrected before the passing full gate. No existing no-transcript hook behavior was changed. No model-based behavioral evaluation suite was run for this synchronization.

Source compatibility and local client fixtures do not establish real OAuth, desktop rendering, deployed hook trust, or production authorization. No real Pai tool was invoked, no endpoint was authenticated, and no production infrastructure was changed. The sandbox alone installed dependencies and ran clients/tests.
