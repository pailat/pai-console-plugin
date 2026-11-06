---
description: Park a task so the dispatcher stops counting it
argument-hint: <ISSUE-ID>
allowed-tools: Bash
---

Park the task `$ARGUMENTS`.

1. Run `${CLAUDE_PLUGIN_ROOT}/scripts/launch.sh <ISSUE-ID> --park`. It marks the registry entry parked and records the event; it touches no process.
2. Keep the stream and the recorded session id: `/resume` needs them.
3. Write one line on why it is parked and what unblocks it in your status notes.
