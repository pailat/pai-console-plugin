---
description: Close a task from its recorded run and post the three-line status
argument-hint: <ISSUE-ID>
allowed-tools: Bash
---

Close the task `$ARGUMENTS`.

1. Run `${CLAUDE_PLUGIN_ROOT}/scripts/task-done.sh <ISSUE-ID>`. It closes only a run whose stream ended with a successful `result` frame and exit code 0. Exit 1 means failed and exit 3 means blocked on a permission: report the printed reason and do not close.
2. Ask the gate for the exact pushed sha with `/gate` before you call the work done.
3. Post the status: `${CLAUDE_PLUGIN_ROOT}/scripts/linear-status.sh <ISSUE-ID> --from-run`. It prints the three lines (Done, Next, Blocked) and posts them only when the Linear token and endpoint env vars are set.
