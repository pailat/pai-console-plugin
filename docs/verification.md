# Compatibility verification

Verified on 2026-10-17 using Linux, Codex CLI 0.163.0, and the installed Claude Code CLI. Implementation was coordinated through Herdr with three GPT-6.1-Sol agents and an independent review of runtime and packaging.

## Automated results

- `make check`: 99 tests discovered, 98 passed, one opt-in native probe skipped by default. Package byte reproducibility and the English authoring check passed, with zero language findings.
- `PAI_RUN_CODEX_RUNTIME=1 python3 -m unittest discover -s tests -p test_codex_runtime.py -v`: the optional probe passed separately. It uses a temporary Codex home, local mock model and local mock MCP, with no bypass flags or credentials. Known reads `whoami` and `page_read` ran; `page_update` and unknown `future_write` prompted. Rejecting both resulted in zero received writes. The server identity was `pai_console_production`.
- All four Claude strict validations passed: marketplace/root, plugin manifest, skills and agents.
- The mocked Claude `erd-from-description` evaluation passed at 1.00: search order, model-before-entities order, typed columns, FK columns, sources, no manual edges and final diagram verification. This is one behavioral regression case, not a claim that the entire evaluation suite was run.
- All 15 translated example files passed the actual pai-portal contracts from archived revision `a4ece4fcf`, including C4, ERD, flows, pages/HTML, tasks, screens, themes and views. Dependencies were installed only in a temporary snapshot; the external pai-portal checkout was not changed.
- English reference generation succeeded against the same archived contracts using `--references-only --source-revision a4ece4fcf`. Source hashes bind reviewed translations to their input prose. Literal upstream JSON examples remain source data.
- `hooks/hooks.json`, `hooks/tools.json` and `evals/mocks/pai/_tools.json` remain byte-for-byte identical to the original revision. Claude write confirmation behavior remains covered by regression tests.

Helper tests include idempotent switching, unrelated TOML/comment preservation, exact approval identities, Git marketplace snapshots, ordinary-failure rollback, preservation of concurrent external edits, and refusal to replace symlinked or dangling configuration files.

## Public OAuth discovery

Read-only unauthenticated GET checks passed for staging, develop and production:

- Each corporate MCP returned HTTP 401 and advertised protected-resource metadata matching its endpoint.
- Each issuer advertised a dynamic registration endpoint, PKCE S256, authorization_code and refresh_token grants, and scope `pai:manage`.
- Staging points to `https://console-staging-e31f.up.railway.app`; develop to `https://console.paitesting.com`; production to `https://console.pai.lat`.

No OAuth clients were registered, no users signed in, and no project writes were made by these checks. Discovery alone does not verify callback acceptance, token refresh or account permissions.

## Remaining installed-client checks

Before declaring a production installation fully verified, complete OAuth per endpoint, review/trust the exact installed hooks, and test desktop presentation and configuration precedence. Verify a harmless authorized write in nonproduction, and cancel a production approval before execution. Check switching after a restart and confirm the selected server with `whoami`.

Unique Codex server names prevent accidental overlap between environment variants and generic `pai` connections. They are not a security boundary against someone changing trusted local configuration or installing a colliding server. Hooks provide workflow guardrails; server authorization, CAS and idempotency remain necessary.
