---
description: Resume a parked or blocked task by its recorded session id
argument-hint: <ISSUE-ID> [pane]
allowed-tools: Bash
---

Resume the task `$ARGUMENTS`.

1. Check the recorded state: `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --status`. A blocked run needs its permission decision from your parent first.
2. Run `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --resume [--pane <pane>]`. It continues the recorded session with `claude -p --resume` and rewrites the state file.
3. The exit code is the verdict, as in `/task-start`: 0 done, 1 failed, 3 blocked.
