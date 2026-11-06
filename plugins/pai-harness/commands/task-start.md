---
description: Start one issue as a headless `claude -p` run, recorded in the state dir
argument-hint: <ISSUE-ID> <prompt-file> [queue]
allowed-tools: Bash
---

Start the task `$ARGUMENTS` (issue id, prompt file, optional queue from `[queues]`).

1. Check capacity first: `${CLAUDE_PLUGIN_ROOT}/scripts/dispatcher.sh --queue <queue> --dry-run` with the one ready line `<ISSUE-ID> prompt-file=<file>` on stdin. If the issue is skipped, report why and stop.
2. Launch it: `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --prompt-file <file> --queue <queue> [--pane <pane>]`. A run is never hidden: with `--pane` it runs in that pane (use a pane you own, since its tab is renamed); inside Herdr without `--pane` the launcher opens its own tab; outside Herdr it runs in your terminal. In all three the pane prints one line per event (init, each tool call, assistant text, the result with turns, duration and estimated cost) from `render_stream.py`, the stream is also written to `runs/<ISSUE-ID>.jsonl`, and in Herdr the workspace shows `state`, `task`, `run`, `step` and `turns` (source `pai-harness`, 2-minute TTL, cleared on exit) and the tab reads `<ISSUE-ID> · <state>`. This display is for humans: it never decides anything.
3. The launcher loads this plugin into the run (`--plugin-dir` from its own location, unless the plugin is installed) and checks the run's first `system/init` event: the pai-harness plugin, all its skills, and the SessionStart, Stop and PreToolUse hooks (read from the loaded plugin's hooks.json, since init has no hooks field). If any is missing, or init is late or absent, it kills the run by its PID, appends a `BLOCKER` line to the state journal, prints it and exits 1. Treat that as a BLOCKER; do not relaunch without the plugin.
4. The exit code is the verdict: 0 done, 1 failed, 3 blocked on a permission. State comes only from the stream-json `result` frame and the exit code, never from the Herdr agent status of the pane or the metadata above.
5. Report the recorded state with `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --status`.

## Mechanical lane

For the same small edit across several known files, start a mechanical run instead of a normal one: `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --profile mechanical --files <file> [<file> ...] --instruction "<exact instruction>"`, run from a clean git worktree (or pass `--cwd`). The input is a closed brief (no `--prompt`, `--prompt-file`, `--allowed-tools` or `--resume`). The profile fixes: Haiku (`--model sonnet` to opt in), `--strict-mcp-config` with an empty MCP config (no Pai MCP, token or OAuth server), `--tools`/`--allowed-tools` Read, Edit, Grep, Glob, a low `--max-turns` and `--max-budget-usd` (12 and 0.25 by default, `[role_limits.mechanical]` to change) and `--output-format json`. With json output there is no init event, so the plugin self-check is skipped; the verifier is the guard.

Then `${CLAUDE_PLUGIN_ROOT}/scripts/verify-mechanical.sh <ISSUE-ID> --check "<project check>"` (or `--gate <name>`). It passes only when the run is `done`, the diff touches only the listed files and every check exits 0; otherwise it restores the changed paths, reports a `BLOCKER` line and exits 1. One passing run in five is marked `SONNET REVIEW REQUIRED`: review `git diff <base>` with Sonnet, then close with `task-done.sh <ISSUE-ID> --sample-reviewed`. `task-done.sh` refuses a mechanical run without a passing verdict.

Use a script for fully deterministic changes and an interactive session for issues, reviews and decisions.

Add `--dry-run` to any script to see its plan without side effects. Never pass a permission-bypass flag: a run that needs a permission must end blocked.
