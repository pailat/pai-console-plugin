# Pai Console integration checkpoint for 0.0.9

The reviewed source is the published `feat/0.2.5/reui` revision [203000f869ef56f22da8a18e0f2e51a48a2293cd](https://github.com/pailat/pai-portal/commit/203000f869ef56f22da8a18e0f2e51a48a2293cd), observed on 2026-10-18. An exact Git archive under /tmp supplies contracts and the in-memory MCP registration. Existing dependency artifacts are linked into that snapshot; no external source checkout, database, user configuration or infrastructure is modified. Unpublished commits from a developer worktree are outside this checkpoint.

## Inventory and compatibility

The previous plugin inventory had 234 tools. This checkpoint has 280 tools, comprising 110 annotated reads and 170 writes. It adds 54 names and removes eight CRM aliases. The generator uses a synthetic inventory actor with upstream-defined platform-admin permissions and evaluator flags, not a live account or an admin-role authorization bypass. tools/list never accesses a store in this verification. Generation fails on missing/duplicate names, unexpected names, pagination that would truncate the snapshot, or missing read annotations.

The upstream declaration has 282 names; proposal_accept and proposal_reject are intentionally client-only and excluded from the corporate actor. Individual users can have a much smaller discovery surface. Visible tools do not establish authorization on a particular resource. A 404 can deliberately conceal inaccessible resources; neither a staff label nor a role name authorizes trying another identity.

Retired names are crm_lead_task_create, crm_lead_task_complete, crm_task_create, crm_task_get, crm_task_list, crm_task_update, crm_task_complete and crm_task_tag_list. Their replacements use task_* with crm.tasks.* grants. Nested CRM firstTask/task/nextTask envelopes still use body; unified task endpoints use title and completion next. Historical translation catalogs remain historical source translations, not current operational instructions.

## Added capabilities

- Unified tasks: task_list_mine, task_list, task_get, task_tag_list, task_create, task_update, task_complete, task_cancel, task_archive and task_restore. Shared tasks/schedule/CRM/product workflows distinguish primary contexts, CRM follow-up requirements, date-only project tasks, agent proposals, revisions and final states.
- Owned Pai Agent chats: chat_list, chat_get, chat_create, chat_close, chat_send and chat_cancel. Sending charges organization credits; timeout does not mean a turn stopped. Closing is final and revokes chat tokens. Published chat_send accepts message text; no fabricated approval-response payload is sent when approval must be handled in Portal.
- IAM: principal/group/member/role discovery and changes, permission catalog, policies/bindings, denies, organization boundaries, access tests/explanations, audit, Pai access pagination and visibility settings. Full policy replacement preserves unrelated explicit bindings and uses current etag. Diagnosis never authorizes an access grant.
- Knowledge: knowledge_move and knowledge_merge, including atomic containment subtrees, product constraints, released page provenance, two-node CAS for merge, edge evidence and manual review of pages citing the historical duplicate. Client-visible graph changes remain restricted.
- Resources: folder_reorder is a complete manual-order replacement of direct children, including an empty array to clear it. Upload workflows cover MCP-origin expiring single-use tickets, exact bytes/headers, inline original-file checksums, host-supplied chat attachments, idempotent asset finalization and Portal fallback.
- Privacy: crm_lead_anonymize and crm_submission_anonymize require explicit ARCO intent and preserve the server's retained metrics/history contract. organization_domain_set changes suggestions without automatically linking leads.

## Existing schema changes

Exact generated schemas are refreshed for asset_upload, file_upload, crm_lead_create, crm_lead_create_from_submission, crm_lead_import, crm_lead_qualify, crm_lead_update, crm_organization_list, flow_create, flow_save, knowledge_context, knowledge_view, organization_theme_preview, organization_theme_save_draft and product_update. Tool descriptions, annotations and metadata are retained literally from tools/list, including descriptions whose source language is Spanish.

Maintained workflow prose and generated reference prose remain English. Source hashes bind the new reference translations to reviewed inputs, including inline Knowledge citation rules and PRD v2. API identifiers, enums, literal error messages and upstream examples are preserved.

Claude installation, configurable endpoint and agent names remain intact. Its explorer allowlist now uses current read-only tools. Both client adapters enforce search-before-create for the added task/chat/IAM creation families. Codex still uses unique pai_console_environment servers and native production approval policy; restricted CRM/IAM/task users can work against the fixed package endpoint when whoami is not exposed. A recorded environment mismatch blocks all writes. No Codex hook emits an ask decision.

## Source capabilities without a new MCP operation

Workforce UI, My Projects kanban styling, collaboration migration fencing and internal Pai Agent model/approval UI changes exist in upstream. This plugin exposes the actual published MCP surface and documents relevant permission/approval effects; it does not add fictitious Workforce endpoints, rebuild Portal UI or accept unpublished chat payloads. Use Portal for operations without an exposed tool and verify environment deployment before claiming availability.

## Reproduction

```bash
PAI_PORTAL=/path/to/exact-upstream-snapshot bun tools/gen-references.ts --source-revision 203000f869
PAI_PORTAL=/path/to/exact-upstream-snapshot bun tools/validate-examples.ts
make build
make check
PAI_RUN_CODEX_RUNTIME=1 python3 -m unittest discover -s tests -p test_codex_runtime.py -v
claude plugin eval . --case unified-task-completion --runs 1 --ablation none --mocks record --allow-tools 'mcp__plugin_pai-console_pai__*' --trust-plugin --no-publish
```

The MCP fixture is compact literal JSON to remain below Claude's 1 MiB mock-file limit without discarding descriptions or input fields. A regression verifies that limit and annotation parity with policy inventory. Behavioral evaluations use local stand-ins and never real project writes. See [verification](verification.md) for current results and the remaining OAuth, desktop and deployment checks.
