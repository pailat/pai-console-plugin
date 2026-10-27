# Pai Console integration checkpoint for 0.0.10

The reviewed source is `pai-portal` [`release/0.2.5` at `a1185b46b`](https://github.com/pailat/pai-portal/commit/a1185b46b), observed on 2026-10-27. It contains every merge since the 0.0.9 checkpoint ([`203000f869`](https://github.com/pailat/pai-portal/commit/203000f869ef56f22da8a18e0f2e51a48a2293cd)), including #251, #257, #267, #268, #269, #270, #279, #281, #291, #293 and #294 (an agent test, no contract change). A `git archive` of that commit under the session scratchpad, with dependencies installed there by `bun install --frozen-lockfile --ignore-scripts`, supplies the contracts and the in-memory MCP registration. No pai-portal checkout, database, user configuration or infrastructure was modified, and no MCP tool was called against any environment: the guidance is written from source code.

An earlier pass of this sync used `8319d44d2` (contract identical to `ec3fc47c8`, used by #10). Moving to `a1185b46b` adds #268, #293 and #294.

## Pai Agent turns (#268)

#268 changes no chat_* MCP contract; its effects reach MCP callers through `status`, `reply`, chat_get messages and traces. The `chats` skill now documents:

- **Per-turn credit budget (K1).** With `HIVE_TURN_MAX_CREDITS` set (500–100000; unset means no ceiling, the owner's value is 12000), Pai Agent estimates each step's cost and, when the next one would not fit, takes a last tool-free step to summarize. chat_send returns `completed` with the literal ending «Cerré aquí este turno al llegar a su presupuesto de créditos…». The closing step may exceed the ceiling but never the balance; a pending approval takes precedence. No field reports the budget or credits used per turn.
- **Single readable ending.** Failed turns (time or token limit, service restart, provider error, failure before the first step) return `failed` with exactly one ending text and `metadata.pai.ending {turnId, text}`; cancellation adds none.
- Read results kept for the turn (16000 characters) and `tools_load` with `query` only change what traces and saved tool parts show.

## API Design cut 2 (#293)

- `api_design_review` (rules on a saved revision) and `api_design_scaffold` (OpenAPI draft from an ERD data model, no write) are new reads.
- Create and save run ruleset version 1: `error` findings block with `API_DESIGN_RULES` and `cause.findings`; warnings and info come back in the write result. Unchanged saves of older designs are not refused.
- Saves derive `uses` edges from the `api` node to the entities and components named by `x-pai-entity`/`x-pai-component`; unresolved or wrong-kind references are warnings.
- New page block `api {id, type, apiDesignRef, revision?}` with `API_DESIGN_NOT_FOUND`, `API_DESIGN_NOT_A_DESIGN`, `API_DESIGN_ARCHIVED`, `API_DESIGN_REVISION_NOT_FOUND` and the warning `API_DESIGN_NOT_CLIENT_VISIBLE`; `page_read` adds `apiDesigns`. `api_design_mock` answers 2xx without content empty.
- The page content schema (page_create, page_update, page_suggest, proposal_save) gains the block; the ontology and page-type references gain two reviewed translations (`tools/reference-translations-sync-a1185b46b.json`).

## Inventory

302 tools (122 reads, 180 writes) for the synthetic platform-admin inventory actor, versus 280 in 0.0.9: 22 added, none removed. Upstream declares 304 names; `proposal_accept` and `proposal_reject` remain client-only.

| Added tool | Skill |
|---|---|
| `api_design_list`, `api_design_get`, `api_design_export`, `api_design_mock`, `api_design_review`, `api_design_scaffold`, `api_design_create`, `api_design_save` | `api-design` (new) |
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

## Full tool coverage

Thirty-five tools that predate 0.2.5 were listed in `skills/pai-console/references/tools.md` but named by no workflow. They now have guidance with the same standard (when to use, search first, confirmation, literal errors, irreversibility), written from release source:

- New `organizations` skill: `organization_member_role_set`, `organization_member_remove`, `organization_invitation_cancel`, `project_invite_client`, `organization_slug_set`, `project_slug_set`, `project_status`, `brief_list`, `brief_get`, `brief_agenda`, `brief_update_status`, `agent_list`, `agent_get`, `agent_update`, `agent_delete`, `credit_transactions`, `me_profile_update`, `me_avatar_upload_url`.
- `crm`: `crm_opportunity_contact_primary`, `crm_opportunity_contact_remove`. `products`: `product_environment_remove`, `product_link_remove`, `product_unlink_project`, `product_member_update`, `product_member_remove`. `schedule`: `milestone_get`, `milestone_dependency_update`, `milestone_dependency_delete`, `task_dependency_update`, `task_dependency_delete`. `knowledge`: `knowledge_unlink`. `resources`: `comment_create`, `comment_history`, `file_get`, `file_download_url`.

`tests/test_skill_refs.py` now fails if any inventory tool is not named in a `SKILL.md`. The new `org-invite-pending` evaluation covers the `organizations` skill.
