---
description: Start one issue as a headless `claude -p` run, recorded in the state dir
argument-hint: <ISSUE-ID> <prompt-file> [queue]
allowed-tools: Bash
---

Start the task `$ARGUMENTS` (issue id, prompt file, optional queue from `[queues]`).

1. Check capacity first: `${CLAUDE_PLUGIN_ROOT}/scripts/dispatcher.sh --queue <queue> --dry-run` with the one ready line `<ISSUE-ID> prompt-file=<file>` on stdin. If the issue is skipped, report why and stop.
2. Launch it in a Herdr pane you own: `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --prompt-file <file> --queue <queue> --pane <pane>`. Without a pane the run is inline in your shell, so use a pane for anything long.
3. The exit code is the verdict: 0 done, 1 failed, 3 blocked on a permission. State comes only from the stream-json `result` frame and the exit code, never from the Herdr agent status of the pane.
4. Report the recorded state with `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --status`.

Add `--dry-run` to any script to see its plan without side effects. Never pass a permission-bypass flag: a run that needs a permission must end blocked.
