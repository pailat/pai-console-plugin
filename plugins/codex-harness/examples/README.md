# Examples

`acme/.pai-harness.toml` is a complete project config for the fictional Acme project.

## Permission policy

The permission policy of the pai-harness plugin (`--permission-mode bypassPermissions`, `permissions.deny` rules, the deny-baseline
check) is Claude Code only. `scripts/launch.py` and its `[run]` keys drive `claude -p`; they do nothing for Codex, and this package
ships no Claude settings files. Codex has no deny-rule layer: configure native MCP approval policies in the Codex client, treat
unknown tools and environments conservatively, and do not claim that approvals or hooks work before testing the installed client.
