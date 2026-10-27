# Compatibility verification

## 0.0.10 (Pai Console 0.2.5 release)

Verified on 2026-10-27 on Linux with Codex CLI 0.164.0 and Claude Code CLI 2.1.311 against pai-portal `release/0.2.5` at `8319d44d2` ([integration checkpoint](upstream-sync-0.0.10.md)). The snapshot is a `git archive` in a session scratchpad with dependencies installed there; no pai-portal checkout was modified and no MCP tool was called against any environment.

- `tools/gen-references.ts`: full generation (references, `hooks/tools.json`, the literal mock inventory) succeeded with 300 tools; a second run produced identical bytes.
- `tools/validate-examples.ts`: 19 example files, 0 failures, including the new `api-design/examples/list-designs.json` checked against the upstream `apiDesignListQuerySchema`.
- `make build` and `python3 tools/build_codex.py --check`: the three Codex packages are byte-reproducible.
- `python3 tools/check_english.py`: 0 findings across 389 files.
- `PAI_RUN_CODEX_RUNTIME=1 python3 -m unittest discover -s tests`: 104 tests, 0 failures, 0 skips. The native probe again received only whoami and page_read; page_update and future_write prompted and were rejected, with zero writes received.
- `claude plugin validate --strict` passed for the root, the manifest, `skills` and `agents`.
- `claude plugin eval . --ablation none`: all 18 cases scored 1.00 (2 runs each, 1 for unified-task-completion), with local mock stand-ins only. The three new cases also ran with the no-plugin baseline arm: api-design-save-existing 1.00 vs 0.40, chat-approval-needs-user 1.00 vs 0.00, prd-confirm-is-human 1.00 vs 0.67.
- Before this sync, render-payments-summary, view-page-canvas and theme-brand-draft already failed LLM graders on the base commit `db3c26c`. Clearer `views` guidance (status components, canvas `schemaVersion: 1`) and `theme` guidance (fix the key named in a contrast issue's `path`) made them pass. page-attributes-filters failed once because its simulated server rejected a valid owner; its mocks now list the valid owner ids.

These are simulated and source-level checks. OAuth, desktop hook trust, effective native approval prompts and live environment availability still need the installed-client checks below.

## 0.0.9

The 0.0.9 upstream integration was verified on 2026-10-18 on Linux with Codex CLI 0.163.0 and Claude Code CLI 2.1.302. Source compatibility is pinned to published pai-portal revision `203000f869ef56f22da8a18e0f2e51a48a2293cd`; see [integration details](upstream-sync-0.0.9.md). The initial Claude/Codex refactor was reviewed separately before this synchronization.

## Automated results

- `make check`: 104 tests discovered, 103 passed, one opt-in native probe skipped by default. Package byte reproducibility and English authoring checks passed with zero language findings.
- `PAI_RUN_CODEX_RUNTIME=1 python3 -m unittest discover -s tests -p test_codex_runtime.py -v`: the native probe passed separately. It uses a temporary Codex home, local mock model and local mock MCP, with no bypass flags or credentials. Known reads whoami and page_read ran; page_update and unknown future_write prompted. Rejecting both resulted in zero received writes. Server identity was pai_console_production. This is native client enforcement against local fixtures, not deployed hook trust.
- All four Claude strict validations passed: marketplace/root, plugin manifest, skills and agents. The three new skills also passed the skill-creator metadata validator.
- All 18 example files passed actual pai-portal contracts from archived revision 203000f869, including new unified-task creation, owned-chat listing and IAM access-test examples. Nested inputs for the new examples use the actual upstream Zod contracts. The snapshot under /tmp links existing dependencies without modifying an external checkout.
- Full English reference and literal inventory generation succeeded against that snapshot; regenerating both a second time produced identical bytes. The in-memory tools/list has 280 tools and matches all corporate names in the upstream declaration; the two client-only proposal operations are deliberately excluded. Source hashes bind reviewed reference translations. Literal upstream schemas/descriptions/examples retain their original content and language.
- Claude's tool fixture remains below its 1 MiB mock-file limit using compact JSON without removing contract data. Regression coverage checks the size, annotations, retired aliases, search-before-create in new domains and native policy generation for new IAM/chat/task/privacy writes.
- The original Claude hooks declaration is unchanged. Shared policy and inventory intentionally include current upstream operations; the Claude explorer still permits only annotated reads. Production writes continue to prompt, with regression coverage for anonymization, IAM policy replacement and credit-charging sends.

## Mocked behavioral evaluations

The unified-task-completion and crm-link-needs-join cases each passed at 1.00 with one run, local MCP stand-ins, no baseline arm and no published report. Task evaluation confirms task_list → task_get → task_complete with expectedRevision 7, no duplicate creation and no Knowledge resolution. CRM evaluation uses actual granular permission identifiers and confirms that missing iam.staffAssignments.create does not justify creating a duplicate organization. These are simulated behavioral regressions, not live authorization checks or an exhaustive suite.

The updated erd-from-description evaluation also passed at 1.00 with one mocked run: search order, model-before-entities order, typed columns, FK columns, sources, no manual edges and final diagram verification. These three cases do not establish that the entire evaluation suite passed.

Helper tests include idempotent switching, unrelated TOML/comment preservation, exact approval identities, Git marketplace snapshots, ordinary-failure rollback, preservation of concurrent external edits, and refusal to replace symlinked or dangling configuration files.

## Public OAuth discovery

The refactor baseline on 2026-10-17 included read-only unauthenticated GET checks for staging, develop and production; these were not rerun as part of the 2026-10-18 source sync:

- Each corporate MCP returned HTTP 401 and advertised protected-resource metadata matching its endpoint.
- Each issuer advertised a dynamic registration endpoint, PKCE S256, authorization_code and refresh_token grants, and scope `pai:manage`.
- Staging points to `https://console-staging-e31f.up.railway.app`; develop to `https://console.paitesting.com`; production to `https://console.pai.lat`.

No OAuth clients were registered, no users signed in, and no project writes were made by these checks. Discovery alone does not verify callback acceptance, token refresh or account permissions.

## Remaining installed-client checks

Before declaring a production installation fully verified, complete OAuth per endpoint, review/trust the exact installed hooks, and test desktop presentation and configuration precedence. Verify a harmless authorized write in nonproduction, and cancel a production approval before execution. Check switching after a restart and confirm the selected server with `whoami`.

Unique Codex server names prevent accidental overlap between environment variants and generic `pai` connections. They are not a security boundary against someone changing trusted local configuration or installing a colliding server. Hooks provide workflow guardrails; server authorization, CAS and idempotency remain necessary.
