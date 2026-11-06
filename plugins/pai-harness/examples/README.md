# Examples

- `acme/.pai-harness.toml`: a complete project config for the fictional Acme project.
- `settings.deny.json`: the `permissions.deny` baseline for every role (Acme only, no real names or paths).
- `settings.deny.non-merge.json`: the merge and protected-branch denials for every role except the integrator and orchestrator.

## Permission policy

Every pai-harness role runs with `--permission-mode bypassPermissions`. `launch.sh` and `/task-start` pass it by default; a project opts out with `[run] bypass_permissions = false` in `.pai-harness.toml`. Bypass removes permission prompts, which stalled the fleet; it does not remove process.

Bypass auto-approves every tool that a deny rule does not stop, including every MCP tool, so the safety is two layers, and the first is checked:

1. **Deny rules** (`permissions.deny`, user, project, local or managed settings). `launch.sh` reads the effective settings before a bypass run and, unless the baseline is present, ends the run `blocked` with a named BLOCKER (exit 3) and starts no process; this also applies to `--resume`. The baseline is the git, `rm`, privilege and secret-read rules and the Pai write tools on the `pai` MCP server (`deny_baseline.py`). Copy `settings.deny.json` into `.claude/settings.json` (project) or `~/.claude/settings.json` (user). It also denies the other Pai tools that change access, deploy, delete or export data (IAM, products, members, CRM purge, `user_ban`) under both the `pai` and the plugin server names, and Linear deletes. A run that needs one of them ends `blocked`; do the action by hand or with a parent's explicit decision outside the run. To waive the check, set `[run] require_deny_baseline = false` where another control already denies these actions.
2. **Plugin PreToolUse hooks**: write zones, the push queue guard and the git guardrails (see `hooks/README.md`). Hooks see Bash, Edit and Write calls, never MCP calls.

Deny patterns match the whole command with `*` as a wildcard, so the example covers `git -C repo reset --hard`, `git -c k=v push --force`, `rm -r -f ~`, `rm -rf "$HOME"`, `rm -rf ./.git` and `cat .env`. They are still best effort: a command can read a secret through an interpreter (`python -c`), a variable or a script, and no pattern list closes that. Treat the lists as a baseline to extend, not as proof.

`--allowed-tools` limits nothing while bypass is on, so per-role allow-lists only bind where a project opts out. With the opt-out, `claude -p` has no prompts: a tool that is not pre-approved is denied and the run ends `blocked`.

### Roles that merge

`settings.deny.json` does not deny `gh pr merge` or pushes to protected branches, because the integrator and orchestrator merge by design. Add `settings.deny.non-merge.json` (replace `main`, `master` and `release/*` with your protected branches) to the project settings of every other role's worktree. The preflight does not require it, because only settings per working directory can tell the roles apart.

A denied action is never worked around: do not edit settings, deny rules, hooks or the plugin to get past it. Report a BLOCKER to the parent. Merges still need the orchestrator's explicit line, and ROOT zones still need ROOT GO.
