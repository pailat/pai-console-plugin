---
name: orchestration
description: "Operating method for agents that work under a parent agent in Herdr: no idle waits, the Herdr worktree rule, reporting up a typed orchestrator tree, handoff on close, and the orchestration-wake plugin. Use only when the user or your brief explicitly asks for multi-agent orchestration in Herdr (names a parent agent, or asks you to launch or supervise child agents). Do not use for ordinary Pai tasks."
metadata:
  compatibility: "Herdr 0.9+ with the herdr skill"
---

# Agent orchestration

This skill is the short operating method. Your brief and your organization's decision records are the source of truth for roles, names and process: read them first and follow them when they differ from this text. When you need their records, use the `pai-console` skill to find the organization and project; cite a record instead of copying it. Load the `herdr` skill for every pane, tab, workspace and agent command; this skill only says when to use them.

## Never go idle with work in flight

An idle agent wakes only when someone prompts it, so a handed-off job whose finish prompts nobody stalls everything behind it.

1. Arm a wake-up before you go idle. When you have handed work off and have nothing else to do, start a background command (Bash `run_in_background`) that blocks on the event, then end your turn. When it exits, Claude Code re-invokes you.
   - A child agent finishes or asks: `herdr agent wait <child> --until idle --until done --until blocked --timeout 3600000`.
   - A job in a pane: `herdr pane wait-output <pane> --regex "<UNIQUE>_RC=[0-9]+" --timeout 5400000`. The marker is unique to this run, never one already on screen.
   - A verdict file: `until [ -s <path> ]; do sleep 60; done`, only as a background command.
2. Never end a turn with work in flight and no armed wait. Every brief you write for a child repeats this rule, because the child's own idle turn is where a chain stalls.
3. Scripts push. A long job ends by writing its verdict file and prompting whoever requested it: `herdr agent prompt <requester> "<short id> PASS|FAIL <log path>"`.
4. Keep one background `herdr agent wait <child> --until blocked` per active child you supervise, answer approval prompts within minutes, and re-arm the wait after it fires or times out.
5. Keep a pending item in your own queue file, if your brief defines one, so a lost event is still handled. Mark an item that only waits (`[waiting: <who>]`, `[armed: <wait>]`) so periodic nudges skip it.
6. Never run sleep loops in your own turn, never run a long foreground `herdr agent prompt --wait` (the shell tool times out), never re-prompt an agent that is working, and never reuse a marker.
7. A Codex agent cannot be woken by background tasks: its parent arms the wait on it.

## Worktrees

A worktree is entered only through Herdr, which gives it exactly one workspace and one writer.

- Create a new one with `herdr worktree create --cwd <repository>`, or enter an existing one with `herdr worktree open --path <dir>` or `--branch <name>`.
- Never run `herdr workspace create --cwd <worktree>`: it opens a second workspace on a checkout that already has one, so two writers can edit the same files.
- Name the worktree and its branch from the branch name your issue tracker proposes for the issue, so the issue, branch, worktree and pull request share one name.
- Never work in the primary checkout of any repository, including repositories other than the one your task started in. Work on another repository also goes in a Herdr worktree created from that repository.
- One issue is one branch, one worktree and one pull request. Inside it, a sub-issue is a tab and a role is a pane. Keep one writer per worktree.

## Report to your parent

- Your brief names your parent, usually on a `Report to:` line. Report only to it, in one line, and only for: something ready for review, a blocker, a decision you need, or done: `herdr agent prompt <parent> "<your name>: <one line>"`.
- Do not message other teams' agents or work outside your assigned scope; anything across scopes goes through your parent. Address every agent by name, never by pane id.
- An agent on another machine sends the same one-line prompt over `ssh -o BatchMode=yes <host> "herdr agent prompt <agent> '<line>'"`. The host comes from your brief or machine setup, never from this skill.
- Run state-changing or long commands in your terminal pane with a unique marker (`echo <MARKER>_RC=$?`) and wait with `herdr pane wait-output`. Use `git --no-pager` in pane commands.
- Ask your parent before opening a pull request, merging, publishing or changing infrastructure. Send changes that alter what every installation gets (manifests, dependencies, hooks, server configuration) as a patch before you push them.

## Typed orchestrators

Large efforts usually run as a tree of typed orchestrators. Your brief names the actual agents; the pattern is:

- A **top-level coordinating agent** sits above everything. It owns cross-area decisions, anything that changes what every installation gets, and every merge.
- **Area coordinators** (one per area) each own the fronts of one area (for example one product area or the platform). They start and supervise the worktree leads of their area, decide questions inside it, and forward what is sensitive or cross-area to the top-level coordinator.
- **Helpers** serve gates and machines instead of owning fronts: one runs verification gates, prepares the evidence for each merge and runs merges in order, another owns machines and their lanes. Send mechanical requests (run a gate, prepare a merge, install something on a machine) to the helper that owns them, and judgment requests (review, opening a pull request, blockers, cross-area questions) to your parent.
- A **worktree lead** works one issue, keeps its status notes current, and reports only to its area coordinator. Its own agents (writers, reviewers, a terminal pane) report only to the lead.

Report only up your own chain, never to another front's agents or to a level you skipped; anything across worktrees goes through the orchestrator above you. Only the orchestrator merges.

## Session rotation

A long-running agent's context grows until its quality drops. Rotate the session before that happens: write a checkpoint, ask to be relaunched, and continue from the checkpoint in a fresh session.

- **Threshold.** Checkpoint at about 150k tokens of context, at the next natural pause (after a commit, a push or a finished wait), not in the middle of an edit.
- **Resume file.** Write `NOTES-<agent>.md` in your worktree, for example `NOTES-impl-acme-42.md`, unless your brief names another path. Leave it uncommitted. It holds: what is done; what is next; what is blocked and on whom; the branch and the exact sha; open pull requests; the waits you have armed; and the decisions taken, with the reason for each. Write it so a reader with no memory of this session can continue from it alone.
- **Rotate request.** When the file is complete, append one line to the orchestrator outbox and end your turn: `RELAY-REQUEST rotate <machine>: <agent>`, for example `RELAY-REQUEST rotate laptop: impl-acme-42`. The orchestrator side picks the line up and relaunches that agent with `--resume`. You never relaunch yourself.
- **After the relaunch.** The new session reads the resume file first, checks the branch, sha and waits it lists against reality, and then continues. Delete or update the file once the work it describes is done.
- **Quota is a different request.** When an account hits its usage limit, the line is `RELAY-REQUEST SWITCH ACCOUNT <machine>: <who is parked>`, for example `RELAY-REQUEST SWITCH ACCOUNT laptop: impl-acme-42`. The orchestrator side switches the account; you also leave a resume file so the work can continue.

## Closing

No session stays open after its work is done. Before you stop, leave a written handoff where your brief says (usually a comment on your issue): what was done (commits, pull request, sha), verdicts and evidence paths, what is left with follow-up ids, decisions taken and why, and where your status notes are. Then run `herdr agent prompt <parent> "<name>: DONE, handoff posted"`. Ask whoever records decisions to record yours; do not write decision records yourself unless asked.

## The orchestration-wake plugin

The `pai.orchestration-wake` Herdr plugin is the push half of the method: it prompts a parent when a one-shot child finishes or blocks, and a requester when a pane exits. It is a safety net, not a substitute for arming your own wait: when a wait dies or a child exits without anyone watching, the plugin still wakes the parent. It reads Herdr's semantic agent status, so it works for Claude and Codex panes. It never fails a launcher and logs its decisions in its state directory. It never wakes the pane itself or a target whose own parent is that pane, sends a pane's "finished" wake to a target at most once per interval (default 60 seconds; blocked and exited wakes are never held back), does not repeat a `blocked` wake, and caps wakes per source pane and target per hour.

- Install it per machine, never over a live installation: `herdr plugin install pailat/pai-console-plugin/herdr-plugins/orchestration-wake --ref <tag>`.
- Launchers set pane tokens (`role`, `parent`, `requester`, `issue`, `name`, `verdict`, `wake_on_done`) with the plugin's `bin/pai-pane-meta <pane_id> key=value ...` instead of `herdr pane report-metadata`, so the tokens survive a Herdr restart; it caches them per agent name in the plugin config directory (`agents/<name>.json`), so a relaunched agent rewrites its own file. Locate it with `herdr plugin list --plugin pai.orchestration-wake --json`: the plugin directory is `.result.plugins[0].plugin_root`.
- Settings come from the environment, then `config.env` in the plugin config directory (`herdr plugin config-dir pai.orchestration-wake`): `PAI_WAKE_FALLBACK`, `PAI_WAKE_OUTBOX`, `PAI_WAKE_HOSTS` (`alias=ssh-host[:remote-shell]` for remote targets), `PAI_WAKE_SSH_OPTS` (ssh options for them, default `-o BatchMode=yes -o ConnectTimeout=8`), `PAI_WAKE_REMOTE_PATH` (a PATH prefix for the remote `herdr` call), `PAI_WAKE_MIN_INTERVAL` and `PAI_WAKE_MAX_PER_HOUR`. Local Herdr calls use `HERDR_BIN_PATH`.
- The plugin complements the rules above; it does not replace arming your own wait. Codex agents cannot be woken by a background task, so for them the plugin's wake and the parent's armed wait are the only wake-ups.
