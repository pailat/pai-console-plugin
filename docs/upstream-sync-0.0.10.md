# Pai Console integration checkpoint for 0.0.10

The reviewed source is `pai-portal` [`release/0.2.5` at `8319d44d2`](https://github.com/pailat/pai-portal/commit/8319d44d2), observed on 2026-10-27. It contains every merge since the 0.0.9 checkpoint ([`203000f869`](https://github.com/pailat/pai-portal/commit/203000f869ef56f22da8a18e0f2e51a48a2293cd)), including #251, #257, #267, #269, #270, #279, #281 and #291. A `git archive` of that commit under the session scratchpad, with dependencies installed there by `bun install --frozen-lockfile --ignore-scripts`, supplies the contracts and the in-memory MCP registration. No pai-portal checkout, database, user configuration or infrastructure was modified, and no MCP tool was called against any environment: the guidance is written from source code.

The MCP contract at `8319d44d2` is byte-identical to the [`ec3fc47c8`](https://github.com/pailat/pai-portal/commit/ec3fc47c8) snapshot used by ATE-316 (#10): the commits after #267 only change dependencies (#291). Regenerating references changed only their provenance line.

## Not in this checkpoint

pai-portal #268 (Pai Agent: single readable close of failed turns, read-loop fix, and the optional per-turn credit budget `HIVE_TURN_MAX_CREDITS` / K1) is still open against `release/0.2.5`. Release has no `turnBudget`, so the `chats` skill does not describe a per-turn budget or the new turn-ending metadata. Revisit when #268 merges. There is no second API Design cut merged in release; #269 is "corte 1".

## Inventory

300 tools (120 reads, 180 writes) for the synthetic platform-admin inventory actor, versus 280 in 0.0.9: 20 added, none removed. Upstream declares 302 names; `proposal_accept` and `proposal_reject` remain client-only.

| Added tool | Skill |
|---|---|
| `api_design_list`, `api_design_get`, `api_design_export`, `api_design_mock`, `api_design_create`, `api_design_save` | `api-design` (new) |
| `chat_attachment_upload`, `chat_comment_list`, `chat_comment_create`, `chat_comment_reply`, `chat_comment_set_state`, `chat_trace_list`, `chat_trace_get` | `chats` |
| `knowledge_appearance_set`, `knowledge_appearance_remove`, `knowledge_edge_history` | `knowledge` |
| `product_release_plan_list`, `product_release_plan_create`, `product_release_plan_update` | `products` |
| `resource_list` | `resources` |

Upstream `apps/api/test/mcp-portal-parity.test.ts` adds `resource_list`, the Knowledge appearance and edge-history tools, and a check that `chat_send` approval responses stay staff-only (clients do not see the tool). The plugin guidance matches: chat tools are documented as staff-only.

Changed existing tools with guidance updates:

- `chat_send`: `attachmentIds`, `pinned`, `approvalResponse` and `pendingApprovals`; `message` may be empty with attachments. The 0.0.9 statement that approvals are unsupported through MCP no longer holds.
- `view_render`: `source {pageId | path, blockId?}` renders a saved view block; exclusive with `spec`.
- `task_create`, `task_update`: `startHasTime`, `estimatedMinutes`. `milestone_create`, `milestone_update`: `startHasTime`, `endHasTime`, actual-date flags, `estimatedMinutes`, date or date-time values. `task_list_mine`: `includeClosed`.
- Page, note, whiteboard, folder, file, asset, comment, quiz and `agent_inbox` tools: `projectId` is nullable for the organization's General library.
- `crm_opportunity_win` and `crm_opportunity_lose` descriptions (lead conversion per won deal; Discovery outcome).
- Knowledge kind enums gain `api`; IAM permission enums gain `resources.pages.confirmVersion` and `knowledge.apiDesigns.*`. Email patterns changed without behavioral effect.

## Behavior documented from source

- **PRD version confirmation (#267)** is human-only: no MCP tool confirms a page version, agents and impersonated sessions get `HUMAN_CONFIRMS`, a confirmation pins one revision, and Markdown PRDs are not pinnable. MCP page reads do not expose confirmation state; staff see it in `product_get.definition.evidence.prd.confirmation`. New predefined role `resources.prdApprover` (`resources.pages.get`, `resources.pages.confirmVersion`).
- **Definition review (#267)**: advisory `product_get.definition` for draft products, six check codes, never part of `missing[]` or the status gates.
- **API Design (#269)**: `api` nodes are written only by `api_design_*` (`API_DESIGN_OWNED` otherwise), always internal, no duplicate detection on import, CAS on save, network-free mock with status results.
- **CRM (#270)**: unique open opportunity titles (`CRM_OPPORTUNITY_TITLE_TAKEN`), archive/unarchive cascade to tasks, archive state errors, probability reasons in event history, tool discovery driven by granular permissions. The Console calendar's CAS uses the existing task revision; it has no separate MCP surface.
- **Organization resources (#251)**: General library semantics, `resource_list` origins, no closed-project lock or PRD confirmation there, `AGENT_SESSION_SCOPE` inside Pai Agent sessions.
- **Client embeds (#279)**: a client's `page_read` reduces flow or whiteboard blocks with invisible targets to `{id, type}`.
- UI-only: #252 kanban, #281 code copy button, Console screens per verb, calendar drag.

## Guards and agents

`hooks/policy.py` requires `api_design_list`, `chat_comment_list` and `product_release_plan_list` before `api_design_create`, `chat_comment_create` and `product_release_plan_create`, and adds attention notes for `api_design_save`, the appearance writes and `product_release_plan_update`. The Claude explorer allowlist adds the new reads. Native Codex approval policy is still generated from annotations; production writes keep prompting.

## Evaluations

New cases: `api-design-save-existing`, `chat-approval-needs-user` and `prd-confirm-is-human`, with their own mocks; the shared `page_read` mock gains a `prd/checkout` page that `page_list` does not list. Three cases that already failed on the base commit now pass after clearer `views` and `theme` guidance, and the `page_frontmatter_update`/`page_validate` mocks list valid owner ids. See [verification](verification.md).

## Known gaps outside this sync

Thirty-five pre-0.2.5 tools are listed in `skills/pai-console/references/tools.md` but not named in any workflow (for example `brief_*`, `me_profile_update`, `organization_member_*`, some `*_remove` and dependency update/delete tools). They predate 0.2.5 and were left unchanged.
