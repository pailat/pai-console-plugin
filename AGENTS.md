# Repository instructions

## Language and contracts

Write all maintained skills, agent instructions, documentation, comments, plugin messages, manifest descriptions, and synthetic evaluation material in English. This is the project's authoring convention; it does not determine the user's conversation language. Respond in the user's language and preserve Mexican Spanish business formatting, MXN amounts, and America/Mexico_City dates where required.

Do not translate API identifiers, JSON keys, enum values, tool names, URLs, existing public commands, or authentic external/user content. Keep literal server fixtures faithful to their source. Document intentional language exceptions rather than changing a contract to satisfy a language check.

## Compatibility

Preserve the Claude Code plugin's installation, skill names, agents, configurable MCP endpoint, and write confirmations. Codex adaptations must use separate client adapters and generated environment packages while sharing domain workflows and tool inventory.

Never use Codex `PreToolUse` output `permissionDecision: "ask"`: configure native MCP approval policies instead. Do not claim hooks are trusted or approvals work without testing the installed client. Unknown tools and environments require conservative handling.

## Sources and generated files

Keep skill references relative to their skill directory. Preserve CAS, idempotency, authorization, and search-before-create rules. Do not manually edit generated Codex packages; edit their sources and regenerate them. Generated reference documentation must remain reproducible and English, with upstream literal contract data preserved where necessary.

## Verification and collaboration

Run relevant Python tests, package reproducibility checks, language checks, and available client validation before reporting completion. Distinguish simulated verification from real OAuth, desktop, or production verification.

When coordinating agents, assign exclusive file ownership and inspect their changes before integration. Do not revert another agent's work, commit, merge, publish, or mutate infrastructure without task authorization. Use mocks for destructive scenarios.
