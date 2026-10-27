# Pai Console plugins

Pai staff workflows for **Pai Console 0.2.5+**, distributed as the existing Claude Code plugin and three generated portable Codex packages, version **0.0.10**. Both clients share domain skills and the MCP tool inventory. Client adapters keep installation and approval behavior separate.

Codex uses unique connection names: `pai_console_staging`, `pai_console_develop` and `pai_console_production`. Claude retains `pai`.

## Release 0.0.10 (Pai Console 0.2.5)

**Version 0.0.10**, pending its GitHub release. Source: [`pai-portal/release/0.2.5` at `8319d44d2`](https://github.com/pailat/pai-portal/commit/8319d44d2) (after #291), observed on 2026-10-27. Its MCP contracts are identical to [`ec3fc47c8`](https://github.com/pailat/pai-portal/commit/ec3fc47c8) (#267 merged); later commits only change dependencies. This is source compatibility, not a claim that every environment deploys this revision. Pai Agent's per-turn budget and single turn-ending close (K1, pai-portal #268) are **not** in this release branch and are not documented.

The synthetic corp inventory has **300 tools** (120 reads, 180 writes): 20 added since 0.0.9 and none removed. Every new tool now has workflow guidance:

| Area | Upstream | Plugin behavior |
|---|---|---|
| API Design | #269 | New `api-design` skill for `api_design_list/get/export/mock/create/save`: search before import (the server does not detect duplicates), required sources and idempotency key, whole-document save with CAS (`REVISION`), `OPENAPI_INVALID` issues, `x-pai-entity`/`x-pai-component` links to ERD and C4, network-free mocks, and `API_DESIGN_OWNED` for generic Knowledge writes |
| PRD version confirmation | #267 | `resources`: only a person confirms a PRD version from Portal or Console (`HUMAN_CONFIRMS` for agents); confirmations pin one revision; Markdown PRDs are not pinnable; the new `resources.prdApprover` role in `iam` |
| Definition review | #267 | `products`: advisory `product_get.definition` checks before `building`, reported to the user, never treated as a gate |
| Pai Agent chats | #245–#249 | `chats`: attachments (`chat_attachment_upload`, 100 KiB, exact sha256), pending approvals answered only with the user's explicit decision, private comments (`chat_comment_*`) and traces (`chat_trace_*`) |
| Knowledge | 0.2.5 | `knowledge`: shared-node appearances in projects (`knowledge_appearance_set/remove`), edge history, routing of kind `api` |
| Product release plans | 0.2.5 | `products`: internal `product_release_plan_*` with CAS, full-set milestone replacement and literal error codes; plans never deploy |
| Organization library | #251 | `resources`: `projectId: null` for the General library, `resource_list` with origins and no merging of homonyms |
| CRM | #270 | `crm`: lose result (ATE-316), unique open opportunity titles (`CRM_OPPORTUNITY_TITLE_TAKEN`), archive/unarchive with tasks, lead conversion per won deal, probability reasons in history, permission-driven tool visibility, `CRM_LEAD_HAS_CHAIN` |
| Dates and views | 0.2.5 | `schedule`/`tasks`: timed milestone and task starts, `estimatedMinutes`, date order errors, `task_list_mine.includeClosed`; `views`: `view_render` with a saved `source` |
| IAM | #267, #269 | `iam`: `resources.prdApprover`, `resources.pages.confirmVersion` and `knowledge.apiDesigns.*` |

- **CRM: losing a deal reports its Discovery project** (Linear ATE-316). Since pai-portal #270, `crm_opportunity_lose` returns `{ opportunity, discovery }` like `crm_opportunity_win` returns a result object, not the bare opportunity. `discovery.outcome` is `cancelled`, `kept` or `none`; `kept` lists `reasons`, including the new `close_not_permitted` (whoever lost the deal lacks `resourcemanager.projects.close`, so the project is kept). The `crm` skill documents each outcome: report it, never retry the loss when the project is kept, and reopen a cancelled one only on request with `project_reopen`. New mocks and the `crm-lose-keeps-discovery` evaluation cover the `kept` case.
- **Generated references** come from the release snapshot through `tools/gen-references.ts`; only their provenance line changed from `ec3fc47c8`. New evaluations: `api-design-save-existing`, `chat-approval-needs-user` and `prd-confirm-is-human`. Details: [integration checkpoint](docs/upstream-sync-0.0.10.md).

## Release 0.0.9

**Version 0.0.9:** [GitHub release](https://github.com/pailat/pai-console-plugin/releases/tag/v0.0.9), integrated through [PR #9](https://github.com/pailat/pai-console-plugin/pull/9). Includes the Claude/Codex refactor and the published Pai Console integration below. OAuth, desktop presentation and live environment availability still need manual installed-client verification.

The integration source is [`pai-portal/feat/0.2.5/reui` at `203000f869ef56f22da8a18e0f2e51a48a2293cd`](https://github.com/pailat/pai-portal/commit/203000f869ef56f22da8a18e0f2e51a48a2293cd), observed on 2026-10-18. References and examples use that exact archived snapshot, not unpublished changes from another worktree. This is source compatibility, not a claim that every environment deploys this revision.

| Integrated area | Plugin behavior |
|---|---|
| Unified tasks and product backlog | New `tasks` skill; schedule/CRM/product routing, context discovery, fresh revisions, next-step completion, cancel/archive/restore; eight retired CRM task aliases removed |
| Pai Agent chats | New `chats` skill for owned sessions, resume, chargeable sends, timeout/cancel and final closing summaries; approvals unsupported by this MCP schema use Portal |
| Granular IAM | New `iam` skill for diagnosis, groups/roles, bindings/policies, denies, boundaries, settings and audit; actual grants replace role-name assumptions and retired colon-style CRM permissions |
| Knowledge movement and merge | Scope/subtree/page provenance rules, CAS, surviving references and client-visible restrictions; no automatic page rewrites |
| Resources and uploads | Manual folder order, MCP-origin single-use PUT tickets, returned upload.curl, inline bytes/checksums, host attachments, finalization and Portal fallback |
| Privacy and changed contracts | Explicit ARCO anonymization, organization domains, product draft/hosting restrictions, flow canvas/screen states, Knowledge context, PRD v2 and inline citations |

The generated synthetic platform-admin corp inventory contains **280 tools** (110 reads, 170 writes), versus 234 previously: 54 added and eight retired. All 15 changed existing input schemas are refreshed. Upstream declares 282 names; proposal_accept and proposal_reject remain client-only. A real person's effective IAM grants determine their actual tools/list and resource access. Native approval policies use explicit annotations, never tool-name guesses.

See [upstream integration details](docs/upstream-sync-0.0.9.md) and [verification evidence and limits](docs/verification.md). UI-only features without MCP operations, including Workforce management and changes to the My Projects board, are recorded as upstream capabilities rather than fabricated plugin tools.

For every new or changed upstream capability:

1. Record the integrated source revision and actor/environment availability. Review active feature branches as pending until integrated; do not claim unfinished work is deployed.
2. Update shared workflows, contracts, generated references and real tool inventories, including changed schemas/annotations of existing names. If a feature has no MCP contract, record the upstream dependency instead of inventing a tool.
3. Preserve Claude compatibility and apply the corresponding Codex adapter/policy behavior. Keep authorization, search-before-create, CAS, idempotency and production confirmations.
4. Add appropriate examples and regression coverage, regenerate all three Codex packages, then validate against the selected upstream snapshot and installed clients. Previous test passes do not close new integration items.
5. Freeze the release only after the selected source checkpoint and explicitly deferred manual checks have been reviewed.

The skills cover Resources, generative views (`pai-view@1`, `view_render`), Knowledge, ERD, C4, screens, Flows, Schedule, proposals, payments/CFDI, Products, CRM, unified tasks, Pai Agent chats, IAM and organization themes. Use Mexican Spanish business formatting, MXN amounts and America/Mexico_City dates when the task requires them. Maintained instructions and documentation are English; authentic user content, API identifiers and literal upstream fixtures retain their original language.

## Environments and authentication

| Environment | Corporate MCP endpoint | Console |
|---|---|---|
| staging | `https://mcp-edge-corp-staging.up.railway.app/mcp` | Staging Console |
| develop | `https://mcp-corp.paitesting.com/mcp` | `https://console.paitesting.com` |
| production | `https://mcp-corp.pai.lat/mcp` | `https://console.pai.lat` |

Authentication uses OAuth dynamic client registration, PKCE and scope `pai:manage` with a Pai staff account. Organization membership controls access. Tokens belong to their endpoint: authenticate again after changing environments. No credentials are bundled. The helper never authenticates or edits OAuth credentials.

The former develop endpoint, `https://mcp-edge-corp-develop.up.railway.app/mcp`, remains a supported Claude configuration option during migration. Generated Codex packages use the current fixed endpoint.

## Claude Code installation

The private repository remains its own Claude marketplace, `pai-console-plugin`. Configure Git HTTPS credentials if necessary (`gh auth login`, then `gh auth setup-git`).

```text
/plugin marketplace add pailat/pai-console-plugin
/plugin install pai-console@pai-console-plugin
```

Equivalent terminal commands:

```bash
claude plugin marketplace add pailat/pai-console-plugin
claude plugin install pai-console@pai-console-plugin
```

Select an environment with `/pai-console:pai-env`, then authenticate `plugin:pai-console:pai` through `/mcp`. The existing `mcp_url` userConfig remains configurable through the plugin UI or:

```bash
printf '%s' '{"mcp_url":"https://mcp-corp.pai.lat/mcp"}' | claude plugin configure pai-console --values-stdin
```

For a session without installation, run `claude --plugin-dir /absolute/path/to/pai-console-plugin`. The plugin is also listed as `pai-console@pai-marketplace` in the brand-kit marketplace. Update with `claude plugin update pai-console@pai-console-plugin`, then `/reload-plugins`, or enable marketplace auto-updates in `/plugin`. Release detection uses the manifest version.

Claude retains its `pai-explorer` and `theme-designer` agents and its existing hooks. SessionStart reports the environment. PreToolUse requests confirmation for production writes, describes destructive consequences, and enforces search-before-create. Staging and develop do not use production write confirmations. Unknown tools are handled conservatively. Codex adapters do not replace Claude hooks or userConfig.

## Codex installation and switching

Requires Python 3.11+ and a Codex CLI supporting `plugin marketplace add` and `plugin add`. Native installation was tested with **codex-cli 0.163.0**, using an isolated temporary `CODEX_HOME`, without authentication or model calls. Use the native model **`gpt-6.1-sol`** (`codex -m gpt-6.1-sol`).

From a source checkout, inspect the plan and install staging:

```bash
python3 tools/codex_plugin.py status
python3 tools/codex_plugin.py setup staging --dry-run
python3 tools/codex_plugin.py setup staging
```

The helper uses the verified native commands:

```bash
codex plugin marketplace add /absolute/path/to/pai-console-plugin --json
codex plugin add pai-console-staging@pai-console-plugin --json
```

Direct installation makes the package available; run helper setup to apply the environment activation and approval policy. The marketplace at `.agents/plugins/marketplace.json` exposes three local sources, `./plugins/codex/{staging,develop,production}`, with `AVAILABLE` installation, `ON_INSTALL` authentication and `Productivity` category. Each package contains a root `plugin.json`, portable streamable-HTTP `mcp.json`, `environment.json`, shared skills, generated Codex skills, runtime scripts and a bundled helper. CLI 0.163.0 installs this portable layout without a compatibility manifest.

Switch only when explicitly requested:

```bash
python3 tools/codex_plugin.py switch develop --dry-run
python3 tools/codex_plugin.py switch develop
python3 tools/codex_plugin.py switch production --dry-run
python3 tools/codex_plugin.py switch production
```

The helper backs up the original config to a private `.pai-backup-*.toml` file beside `config.toml`, uses atomic replacement, preserves unrelated TOML text and comments, and restores the original config on failure only when it still matches the last recognized helper/native write. If native commands or another writer changed it, the helper preserves current contents and reports the original backup path. A failed install may leave a package cache or partial native configuration; review the backup before restoring it manually. Existing Pai environment entries from other marketplaces are disabled too; unrelated plugins remain unchanged. Unsupported inline definitions of owned settings fail before installation. A lock serializes helper runs; avoid simultaneous edits from other config writers.

`--dry-run` prints the commands and policy without changing configuration or installing plugins. Automatic Git snapshot discovery invokes only native read-only help/list commands; with an explicit `--marketplace-root`, dry runs invoke no CLI commands. `--codex-home /path/to/home` selects an isolated configuration; otherwise the helper uses `CODEX_HOME` or `~/.codex`. `status` reads only that home and reports user-level activation. Trusted project, managed or system settings can affect the effective client configuration.

The bundled `pai-env` and `setup` skills resolve the absolute directory of their loaded `SKILL.md`, then invoke `"$pai_skill_dir/../../tools/codex_plugin.py"`; they do not rely on the session working directory. `pai-env/agents/openai.yaml` sets `policy.allow_implicit_invocation: false` for explicit-only invocation. Setup remains discoverable with `allow_implicit_invocation: true` and its declared onboarding path. The installed helper resolves a configured local checkout or asks `codex plugin marketplace list --json` for the current configured Git snapshot root. It does not guess cache paths or convert Git registrations to local sources. For an explicit local path or a CLI without usable snapshot discovery, pass `--marketplace-root /absolute/path/to/marketplace-root`. For configured Git sources, supply the current native snapshot root from the list output, rather than another checkout. Explicit roots bypass automatic snapshot discovery: the helper validates package identity but relies on the caller to supply the current snapshot. Switching needs the marketplace root containing all three packages; an individual package is self-contained for its own skills, hooks and MCP connection.

Git-backed installation and updates use the native marketplace workflow:

```bash
codex plugin marketplace add pailat/pai-console-plugin --json
codex plugin marketplace upgrade pai-console-plugin --json
codex plugin marketplace list --json
python3 tools/codex_plugin.py setup staging --dry-run
python3 tools/codex_plugin.py setup staging
```

For a packaged helper, substitute its installed path for `tools/codex_plugin.py`. Refresh the Git snapshot with `marketplace upgrade` before setup/switch when you want updated package files. The helper installs from the current snapshot and preserves its configured Git source and ref; it does not fetch a new revision automatically. If discovery is unavailable, copy that marketplace's `root` from the list output and pass it as `--marketplace-root` (required for both dry run and apply in that fallback).

After installation or switching, restart the desktop app or open a fresh session, select the installed plugin's unique `pai_console_<environment>` connection and authenticate manually. Review and trust the packaged hooks in the installed client. Installation does not automatically trust hooks.

Setup and switching reject symlinked `config.toml` files, including dangling links, before running native installation commands. They preserve the link and target; manage those settings through your dotfile source instead. Status remains read-only and can inspect an existing linked configuration.

## Native Codex policy and hooks

The helper writes policy under the exact installed identity:

```toml
[plugins."pai-console-production@pai-console-plugin"]
enabled = true

[plugins."pai-console-production@pai-console-plugin".mcp_servers.pai_console_production]
enabled = true
default_tools_approval_mode = "prompt"

[plugins."pai-console-production@pai-console-plugin".mcp_servers.pai_console_production.tools.page_read]
approval_mode = "approve"

[plugins."pai-console-production@pai-console-plugin".mcp_servers.pai_console_production.tools.page_create]
approval_mode = "prompt"
```

| Tool classification from `hooks/tools.json` | Staging / develop | Production |
|---|---|---|
| Known read | `approve` | `approve` |
| Known write | `approve` | `prompt` |
| Unknown or invalid annotation | `prompt` | `prompt` |

The default remains `prompt`; explicit overrides cover known tools, and stale unknown overrides are reset to `prompt`. All three environment policies are refreshed when switching. The policy key matches each package's unique MCP entry and `environment.json.server_name`. Existing generic `pai` native policy is outside the helper's ownership and remains unchanged. These are native MCP policies, not a Codex PreToolUse `permissionDecision: "ask"` response.

Each package declares its `setup` onboarding skill and explicitly declares `./hooks/codex_hooks.json` under `extensions.com.openai.hooks` and copies the shared policy/inventory with the Codex adapter. Search-before-create depends on reviewed, trusted and running hooks. CAS (`expectedRevision`), idempotency and authorization remain part of the shared workflows and server contracts.

Config inspection, successful CLI installation and simulated hook tests do **not** verify hook trust or effective desktop approval prompts. Hooks require scripts in the execution environment; a web installation does not deploy Python scripts. Hook-bearing packages target supported manual local installations and are not eligible for the public plugin directory under current documentation. Do not assume identical behavior in every client.

## Skills and agents

| Workflow | Capabilities |
|---|---|
| `pai-console` | Environment discovery, authorization, search-before-create, CAS, idempotency, structured errors and citations |
| `resources`, `views` | Pages, HTML and view blocks, projections, whiteboards, assets, comments, filters, generative UI and visual reports |
| `knowledge`, `erd`, `c4`, `screens`, `flows`, `api-design` | Ontology, proposed decisions, data models, architecture, screens, versioned testable flows and OpenAPI 3.1 API designs |
| `schedule`, `proposals-payments`, `products`, `crm` | Milestones/tasks, SOW, CFDI/payments, product operations and CRM workflows |
| `theme` | Complete light/dark organization themes, contrast, shells, preview and confirmed publication |
| `pai-env` | Explicit environment inspection and switching through the client-specific implementation |

Claude domain skills retain `/pai-console:<skill>` invocation and the original agents. Codex generates `setup`, `pai-env`, `pai-explorer` and `theme-designer` as skills alongside shared domain skills. The explorer uses only known reads. The theme designer uses reads and `organization_theme_preview`, stops after at most eight preview attempts, and returns JSON and unresolved issues without saving, publishing or uploading. These Codex skills provide instructions rather than a native per-agent tool sandbox; the native MCP policy still applies. They use the session's native model.

Pai versions below 0.2.5 are unsupported: stop and explain rather than inventing alternate tool contracts.

## Development and verification

See [verification results](docs/verification.md) for the checks actually run and the remaining installed-client checks. The optional native approval probe is reproducible with `PAI_RUN_CODEX_RUNTIME=1 python3 -m unittest discover -s tests -p test_codex_runtime.py -v` and uses only local fixtures.

Repository instructions live in `AGENTS.md`; `.claude/CLAUDE.md` imports `../AGENTS.md` for Claude. Keep this development context in `.claude/`: a root `CLAUDE.md` triggers a strict Claude plugin validation warning. Installed workflows are delivered through skills.

Edit sources, then regenerate packages. Do not edit `plugins/codex/*` by hand. Generated packages embed the helper and runtime scripts; regenerate after any shared skill, reference, helper or runtime change.

```bash
python3 -m pip install -r requirements-dev.txt
make build
make check
# Equivalent individual checks:
python3 tools/build_codex.py --check
python3 -m unittest discover -s tests
python3 tools/check_english.py
```

`--check` compares every generated byte and reports missing, changed or extra package files without writing. The Python suite includes temporary-home helper tests, mocked CLI failure/rollback and policy tests, package portability/reference checks, and a real native plugin install/switch test when `codex` is available. Native tests only register local marketplace files and install cached packages; they do not authenticate or contact Pai through tool calls. Git snapshot discovery and preservation of Git registration are tested with a mocked CLI; live private-Git transport is not verified by those tests. A skipped native test is not native validation.

Run available Claude validation:

```bash
claude plugin validate --strict .
claude plugin validate --strict .claude-plugin/plugin.json
claude plugin validate --strict skills
claude plugin validate --strict agents
```

Upstream reference/schema checks require a pai-portal checkout with dependencies:

```bash
PAI_PORTAL=/path/to/pai-portal bun tools/gen-references.ts
PAI_PORTAL=/path/to/pai-portal bun tools/validate-examples.ts
claude plugin eval . --allow-tools 'mcp__plugin_pai-console_pai__*' --trust-plugin --no-publish -j 4
```

Full reference generation also refreshes `hooks/tools.json` and `evals/mocks/pai/_tools.json`. Preserve literal upstream data and regenerate Codex packages afterward. For a dependencies-only archived contract snapshot, regenerate just references with a recorded revision:

```bash
PAI_PORTAL=/path/to/archived-contract-snapshot bun tools/gen-references.ts --references-only --source-revision 203000f869
PAI_PORTAL=/path/to/archived-contract-snapshot bun tools/validate-examples.ts
```

Integration validation used archived pai-portal revision `203000f869`, with dependencies linked only in a temporary snapshot; all 18 example files passed actual upstream contracts without changing an external checkout. The generator verifies declared-versus-discovered inventory coverage and explicit read annotations. Its literal MCP JSON is compact to fit Claude's 1 MiB mock-file limit, with no schema fields removed. This establishes source compatibility, not live environment availability.

The shared trace evaluator grades normalized Claude/Codex tool calls using PyYAML from `requirements-dev.txt`:

```bash
python3 tools/evaluate_traces.py --client codex decision-stays-proposed /path/to/trace.json
python3 tools/evaluate_traces.py --client claude spanish-locale /path/to/trace.json
```

Trace JSON contains `calls` (each with `name`, `arguments`, and optional `isError`) and `final_response`. Tool-use graders run deterministically; LLM graders are explicitly reported as `review_required`, never silently passed. `evals/spanish-locale` checks the Spanish locale regression. Evals use a simulated MCP or recorded normalized calls and do not establish real production, OAuth, desktop hook trust or native approval behavior.

Manual installed-client checks still required in the desktop client:

1. Discover and install each environment from the local marketplace, including installation in an existing conversation and a fresh conversation. Run the packaged setup skill.
2. Review and trust the exact installed hooks. Verify environment diagnostics, a known read and search-before-create denial/retry in a mock or nonproduction project.
3. Complete staff OAuth for each endpoint; verify organization access and token separation after switching.
4. Verify native approval behavior with an authorized harmless nonproduction write and a production write whose prompt is cancelled before execution. Verify unknown tools prompt using a controlled mock. Do not run destructive tests on real projects.
5. Check project/managed configuration precedence and confirm exactly one effective Pai environment after restart. Test that unrelated plugins and user comments remain intact.

Official references: [Package your plugin](https://developers.openai.com/plugins/build/plugins) and [Model Context Protocol](https://learn.chatgpt.com/docs/extend/mcp). These define portable layout, OAuth declaration, native policy and trust boundaries; the installed client's actual behavior still needs verification.
