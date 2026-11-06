---
name: watcher
description: "Describes the watcher script that checks agent heartbeats; there is no model in the loop. Use when your brief names this role."
---

# Role: watcher

Watcher. It is a script, not a model: the agent file exists so every role has the same shape, and a run never needs it. The script records heartbeats and reports silent agents.

Roles are skill plus agent plus hooks. This skill is the duties; `agents/watcher.md` fixes the model and the tool allowlist; hooks are owned elsewhere. The default model can be overridden under `[models]` in `.pai-harness.toml`.

## Duties

- Record a heartbeat per agent name with `health.sh beat <name>`.
- Report agents whose heartbeat is older than the configured turn timeout with `health.sh check`.
- Make no decisions: it reports facts and never restarts, parks or kills an agent.

## Inputs

Heartbeat files in the state directory and `[limits] turn_timeout_minutes` from `.pai-harness.toml`.

## Quiet-channel report lines

One line per event, nothing else. Report to your parent, never only on your own screen.

- `REPORT watcher: <name> silent for <minutes> minutes`
- `REPORT watcher: all agents alive`

## Scripts and commands

- `${CLAUDE_PLUGIN_ROOT}/scripts/health.sh beat <name>` and `${CLAUDE_PLUGIN_ROOT}/scripts/health.sh check`.
- Its output is the input of the relay and the orchestrator; they decide what to do.
