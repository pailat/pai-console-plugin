# Examples

- `acme/.pai-harness.toml`: a complete project config for the fictional Acme project.
- `settings.deny.json`: the `permissions.deny` baseline for every role (Acme only, no real names or paths).
- `settings.deny.non-merge.json`: the merge and protected-branch denials for every role except the integrator and orchestrator.

## Permission policy

Every pai-harness role runs with `--permission-mode bypassPermissions`. `launch.sh` and `/task-start` pass it by default; a project opts out with `[run] bypass_permissions = false` in `.pai-harness.toml`. Bypass removes permission prompts, which stalled the fleet; it does not remove process.

Bypass auto-approves every tool that a deny rule does not stop, including every MCP tool, so the safety is two layers, and the first is checked:

1. **Deny rules** (`permissions.deny`, user, project, local or managed settings). `launch.sh` reads the effective settings before a bypass run and, unless the baseline is present, ends the run `blocked` with a named BLOCKER (exit 3), records `blocked` in `runs/<ISSUE>.state.json` (so `--status` shows it, keeping the session id) and starts no process; this also applies to `--resume`. The baseline is the git, `rm`, privilege and secret-read rules, the MCP write rules, and, for every role except the integrator and orchestrator, the merge and protected-branch rules (`deny_baseline.py`). Copy `settings.deny.json` (and `settings.deny.non-merge.json` for roles that do not merge) into `.claude/settings.json` of the run's working directory, or into user settings. Both files are generated from `deny_baseline.py` (`python3 tools/build_harness_deny.py`, checked by `make check`).
2. **Plugin PreToolUse hooks**: write zones, the push queue guard and the git guardrails (see `hooks/README.md`). Hooks see Bash, Edit and Write calls, never MCP calls, so for MCP writes the deny rules are the only layer.

How the baseline is judged: a baseline rule is satisfied by an identical rule, a wildcard rule that matches it (`mcp__pai__iam_*`) or a whole-server rule (`mcp__pai`). Project settings count only from the run's working directory. This models Claude Code and has been exercised with simulated settings only, not an installed client.

MCP rules are verb patterns (`*delete*`, `*remove*`, `*revoke*`, `*deploy*`, `*publish*`, `*purge*`, `iam_*`, `finance_*`, `*_ban`, and so on) over the `pai` machine server, the plugin's Pai server, Linear (`delete_*`, `merge_diff`) and Railway, so a new tool with one of those verbs is denied without a list update. With strict MCP in force (`pai.mcp_url` set, the launcher passes `--strict-mcp-config`) only the machine server is loaded and only its rules are required. Without it, user-scope servers are loaded too and the baseline requires the plugin Pai, Linear and Railway rules; other servers (Stripe, Gmail, Drive) are not covered, so deny them by server name (`mcp__<server>`) or set `pai.mcp_url`. A run that needs a denied MCP tool ends `blocked`.

`rm` rules deny only the dangerous whole targets (`/`, `~`, `$HOME`, `..`, `.`, `.git`, system directories), so cleaning `/tmp/x`, `dist`, `./build` or `node_modules` still works. `.env` rules cover the env file and its local, production, development, staging and test variants through the common readers, and leave the example and sample env files readable. Patterns remain best effort: a command can read a secret through an interpreter (`python -c`), a variable or a script, and a shell glob such as `rm -rf /*` is not a whole-target spelling; no pattern list closes that.

`--allowed-tools` limits nothing while bypass is on, so per-role allow-lists only bind where a project opts out. With the opt-out, `claude -p` has no prompts: a tool that is not pre-approved is denied and the run ends `blocked`.

### Roles that merge

`settings.deny.json` does not deny `gh pr merge` or pushes to protected branches, because the integrator and orchestrator merge by design. Add `settings.deny.non-merge.json` (replace `main`, `master` and `release/*` with your protected branches) to the settings of every other role's working directory; the preflight requires it for any role other than the integrator and orchestrator.

A denied action is never worked around: do not edit settings, deny rules, hooks or the plugin to get past it. Report a BLOCKER to the parent. Merges still need the orchestrator's explicit line, and ROOT zones still need ROOT GO.
