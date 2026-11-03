# Pai Console integration checkpoint for 0.0.12

The reviewed source is `pai-portal` `release/0.2.5` at `47f888e08242291e8b2896a67b965a81327616c8` (2026-11-03). The previous reference sync used `dbe7832cb` (README 0.0.11 section); the range holds 132 first-parent merges. A read-only `git archive` of that commit under a scratch directory, with dependencies installed there by `bun install --frozen-lockfile --ignore-scripts`, supplied the contracts and the in-memory MCP registration. No pai-portal primary checkout was modified (only `git fetch` of the release branch and `git archive`/`git log`), no database or user configuration was touched, and no MCP tool was called against any environment.

```bash
PAI_PORTAL=<scratch snapshot> bun tools/gen-references.ts --source-revision 47f888e08
```

One new reviewed translation (`tools/reference-translations-sync-47f888e08.json`) covers the changed `databaseAction` section description. This is source compatibility, not a claim that every environment deploys this revision.

## Inventory

353 tools (141 reads, 212 writes) for the synthetic platform-admin inventory actor; upstream declares 355 names, with `proposal_accept` and `proposal_reject` still client-only. 40 tools are added, none are removed.

| Area | Added tools | Changed contracts |
|---|---|---|
| Pai DB Spaces and records (new `spaces` skill) | `space_create`, `space_update`, `space_list`, `space_schema`, `space_version_create/get/compare/publish/archive`, `space_versions`, `space_deploy`, `record_query/get/create/update/events`, `record_action_run` | Knowledge `action` gains the closed `databaseAction` section |
| IAM | `iam_binding_list_mine`, `iam_binding_renounce`, `iam_service_account_create/disable/get/list/update`, `iam_service_token_create/list/revoke/rotate`, `iam_staff_grant_create/end` | `iam_binding_add` takes `justification`; `iam_binding_remove` takes `etag` |
| Connections (`organizations`) | `connection_enrollment_get/approve`, `connection_terminal_list/terminate` | No tool takes `organizationId`; `connection_list` gains `scope` |
| Project agents | `agent_routine_delete` | — |
| Products | `product_manifest_save`, `product_app_client_register`, `product_version_create/publish` | — |
| CRM | `crm_opportunity_loss_update` | `crm_opportunity_win` gains `delivered`; `crm_lead_workspace_join` takes `leadId` or `opportunityId` |
| API design | — | `api_design_review` gains `compareToRevision`; the ontology lets `api` link to `action` and `screen` |

## Skill and evaluation changes

- New skill `spaces`; changed `iam`, `organizations`, `products`, `crm`, `api-design`, `tasks`, `schedule`, `screens`, `erd` and the base `pai-console` skill (routing, connection errors, secrets that are shown once).
- Task behavior: a new `record` context, read-only tasks of closed projects (`PROJECT_CLOSED`) and banned assignees (`TASK_ASSIGNEE_BANNED`, `OWNER_NOT_ELIGIBLE`).
- The read-only explorer agent gains the Spaces reads, `iam_binding_list_mine`, the service account reads and the connection pairing and terminal reads. It does not get `iam_service_token_list`.
- New evaluations: `space-publish-lifecycle`, `record-update-cas`, `iam-service-token-secret-once`, `connection-terminal-terminate`, `agent-routine-delete-link`, `crm-loss-correction`, `crm-win-already-delivered`, `api-design-compare-breaking`, `product-version-needs-major`, with new mock files for their tools.
- The connection registry test now asserts the released surface of nine tools without `organizationId`.

## Not covered, and why

- **Badges, lead and opportunity record redesign and organization accounts** (ATE-639, ATE-644, ATE-657): Console and domain work with no MCP contract change; the CRM skill records the behavior (every organization has a CRM account) and marks the rest unverified.
- **ATE-679 to ATE-683:** no commits matched in the reviewed range apart from the tools above.
- **Unified `task_create` `responsible` input:** present in the source but absent from the generated index, so it is not documented.
- **Pai DB workflows beyond Spaces and records** (`databases.*` role administration beyond the permission rules in `iam`): not exposed as MCP tools in this snapshot.
- **Evaluations and mocks** are simulations; none ran against a real server or a real model.
- Real OAuth, desktop and production behavior stays unverified here.

## Structure change in the same release (ATE-714)

The same release folds orchestration into the single plugin: `skills/herdr` (vendored upstream, pinned by `vendor/herdr/PIN.json`), `skills/orchestration`, the wake plugin and the `herdr-release-watch` workflow; the `pai-orchestration` and `herdr` marketplace entries are removed. The Codex packages carry both skills with explicit-use-only policy. See [orchestration.md](orchestration.md).
