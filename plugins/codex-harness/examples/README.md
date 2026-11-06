# Examples

- `acme/.pai-harness.toml`: a complete project config for the fictional Acme project.
- `settings.deny.json`: a generic `permissions.deny` list for Claude Code settings (Acme only, no real names or paths).

## Permission policy

Every pai-harness role runs with `--permission-mode bypassPermissions`. `launch.sh` and `/task-start` pass it by default; a project opts out with `[run] bypass_permissions = false` in `.pai-harness.toml`. Bypass removes permission prompts, which stalled the fleet; it does not remove process.

Safety never depends on prompts. Two layers hold in bypass mode:

1. **Deny rules** (`permissions.deny`, user or project settings). Copy `settings.deny.json` and adapt the protected branches: it denies force, delete, mirror, `+refspec` and `--no-verify` pushes, pushes to protected branches, `reset --hard`, `clean -f`, `branch -D`, `checkout .` and `restore .`, `commit --no-verify`, `rm -rf` of `/`, `~`, `$HOME`, `..` and `.git`, `sudo`, `ssh`/`scp`, secret-file reads and destructive `gh` and infrastructure commands.
2. **Plugin PreToolUse hooks**: write zones, the push queue guard and the git guardrails (see `hooks/README.md`).

A denied action is never worked around: do not edit settings, deny rules, hooks or the plugin to get past it. Report a BLOCKER to the parent. Merges still need the orchestrator's explicit line, and ROOT zones still need ROOT GO.
