---
name: orchestration
description: "Work as part of a multi-agent Herdr setup: never end a turn idle with work in flight, report to the parent named in your brief, hand off when you finish, and use the orchestration-wake plugin. Use when your brief names a parent agent, or when you launch and supervise child agents in Herdr."
metadata:
  compatibility: "Herdr 0.9+ with the herdr skill"
---

# Agent orchestration

This skill is the short operating method. Your brief and your organization's decision records are the source of truth for roles, names and process: read them first and follow them when they differ from this text. When you need their records and the pai-console plugin is installed, use its skills to find the organization and project; cite a record instead of copying it. Load the `herdr` skill for every pane, tab, workspace and agent command; this skill only says when to use them.

## Never go idle with work in flight

An idle agent wakes only when someone prompts it, so a handed-off job whose finish prompts nobody stalls everything behind it.

1. Arm a wake-up before you go idle. When you have handed work off and have nothing else to do, start a background command (Bash `run_in_background`) that blocks on the event, then end your turn. When it exits, Claude Code re-invokes you.
   - A child agent finishes or asks: `herdr agent wait <child> --until idle --until done --until blocked --timeout 3600000`.
   - A job in a pane: `herdr pane wait-output <pane> --regex "<UNIQUE>_RC=[0-9]+" --timeout 5400000`. The marker is unique to this run, never one already on screen.
   - A verdict file: `until [ -s <path> ]; do sleep 60; done`, only as a background command.
2. Never end a turn with work in flight and no armed wait.
3. Scripts push. A long job ends by writing its verdict file and prompting whoever requested it: `herdr agent prompt <requester> "<short id> PASS|FAIL <log path>"`.
4. Keep one background `herdr agent wait <child> --until blocked` per active child you supervise, answer approval prompts within minutes, and re-arm the wait after it fires or times out.
5. Keep a pending item in your own queue file, if your brief defines one, so a lost event is still handled. Mark an item that only waits (`[waiting: <who>]`, `[armed: <wait>]`) so periodic nudges skip it.
6. Never run sleep loops in your own turn, never run a long foreground `herdr agent prompt --wait` (the shell tool times out), never re-prompt an agent that is working, and never reuse a marker.
7. A Codex agent cannot be woken by background tasks: its parent arms the wait on it.

## Report to your parent

- Your brief names your parent, usually on a `Report to:` line. Report only to it, in one line, and only for: something ready for review, a blocker, a decision you need, or done: `herdr agent prompt <parent> "<your name>: <one line>"`.
- Do not message other teams' agents or work outside your assigned scope; anything across scopes goes through your parent.
- An agent on another machine sends the same one-line prompt over `ssh -o BatchMode=yes <host> "herdr agent prompt <agent> '<line>'"`. The host comes from your brief or machine setup, never from this skill.
- Run state-changing or long commands in your terminal pane with a unique marker (`echo <MARKER>_RC=$?`) and wait with `herdr pane wait-output`. Use `git --no-pager` in pane commands.
- Ask your parent before opening a pull request, merging, publishing or changing infrastructure. Send changes that alter what every installation gets (manifests, dependencies, hooks, server configuration) as a patch before you push them.

## Closing

No session stays open after its work is done. Before you stop, leave a written handoff where your brief says (usually a comment on your issue): what was done (commits, pull request, sha), verdicts and evidence paths, what is left with follow-up ids, decisions taken and why, and where your status notes are. Then run `herdr agent prompt <parent> "<name>: DONE, handoff posted"`. Ask whoever records decisions to record yours; do not write decision records yourself unless asked.

## The orchestration-wake plugin

The `pai.orchestration-wake` Herdr plugin is the push half of the method: it prompts a parent when a one-shot child finishes or blocks, and a requester when a pane exits. It reads Herdr's semantic agent status, so it works for Claude and Codex panes. It never fails a launcher and logs its decisions in its state directory. It never wakes the pane itself or a target whose own parent is that pane, sends a pane's "finished" wake to a target at most once per interval (default 60 seconds; blocked and exited wakes are never held back), does not repeat a `blocked` wake, and caps wakes per source pane and target per hour.

- Install it per machine, never over a live installation: `herdr plugin install pailat/pai-console-plugin/herdr-plugins/orchestration-wake --ref <tag>`.
- Launchers set pane tokens (`role`, `parent`, `requester`, `issue`, `name`, `verdict`, `wake_on_done`) with the plugin's `bin/pai-pane-meta <pane_id> key=value ...` instead of `herdr pane report-metadata`, so the tokens survive a Herdr restart. Locate it with `herdr plugin list --plugin pai.orchestration-wake --json`: the plugin directory is `.result.plugins[0].plugin_root`.
- Settings come from the environment, then `config.env` in the plugin config directory (`herdr plugin config-dir pai.orchestration-wake`): `PAI_WAKE_FALLBACK`, `PAI_WAKE_OUTBOX`, `PAI_WAKE_HOSTS` (`alias=ssh-host[:remote-shell]` for remote targets), `PAI_WAKE_MIN_INTERVAL` and `PAI_WAKE_MAX_PER_HOUR`. Local Herdr calls use `HERDR_BIN_PATH`.
- The plugin complements the rules above; it does not replace arming your own wait.
