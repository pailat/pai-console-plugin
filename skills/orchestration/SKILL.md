---
name: orchestration
description: "Run or join a multi-agent Herdr orchestration: no idle waits, the communication tree, gate and merge requests, merge packets, DEC-023 handoff closes and the orchestration-wake plugin. Use when you are an orchestrator, a worktree lead or a writer agent working one issue under a parent agent."
metadata:
  compatibility: "Herdr 0.9+ with the herdr skill; Pai 0.2.5+ for the agents-workflow project"
---

# Agent orchestration

This skill is the short operating contract. The source of truth is the Knowledge and Resources of the `agents-workflow` project in Pai Console: read the decisions DEC-021, DEC-023, DEC-027, DEC-028 and DEC-029 there before acting on anything below, and follow them when they differ. Read `../pai-console/SKILL.md` first to find the organization and project, search Knowledge before you capture anything, and never copy decision text into code or briefs: cite the node. Load the `herdr` skill for every pane, tab, workspace and agent command; this skill only says when to use them.

## No idle waits (DEC-029)

An idle agent wakes only when someone prompts it, so a handed-off job whose finish prompts nobody stalls the chain.

1. Arm a wake-up before you go idle. When you have handed work off and have nothing else to do, start a background command (Bash `run_in_background`) that blocks on the event, then end your turn. When it exits, Claude Code re-invokes you.
   - A child agent finishes or asks: `herdr agent wait <child> --until idle --until done --until blocked --timeout 3600000`.
   - A job in a pane: `herdr pane wait-output <pane> --regex "<UNIQUE>_RC=[0-9]+" --timeout 5400000`. The marker is unique to this run, never one already on screen.
   - A verdict file: `until [ -s <path> ]; do sleep 60; done`, only as a background command.
2. Never end a turn with work in flight and no armed wait.
3. Scripts push. Every gate or lane job writes its verdict file and then prompts the requester: `herdr agent prompt <requester> "<sha9> GATE PASS|FAIL <log>"`.
4. Children report up. When done or stuck, run `herdr agent prompt <parent> "<your name>: <one line>"`. The parent is on the `Report to:` line of your brief.
5. Orchestrators keep one background `herdr agent wait <child> --until blocked` per active child and answer approval prompts within minutes. Re-arm it after it fires or times out.
6. Keep a pending item in your own queue file so a lost event is still handled. Mark waiting items `- [waiting: <who>] <item>` or `- [armed: <wait>] <item>`; the periodic tick nudges only plain items.
7. Never run sleep loops in your own turn, never run a long foreground `herdr agent prompt --wait`, never re-prompt an agent that is working, and never reuse a marker.
8. A Codex agent cannot be woken by background tasks: its parent arms the wait on it.

## The communication tree (DEC-021, DEC-027, DEC-028)

owner, then the relay, then the general orchestrator, then an area orchestrator, then the worktree lead `ate-<n>-lead`, then that worktree's writers, reviewers and QA. `integration-orch` runs gates, merge packets and the merge train; `infra-orch` owns machines and lanes; the scribe records decisions.

- Report only to your parent, in one line, only for ROOT ready, a blocker, a decision needed, or DONE. Never message another worktree or the relay; anything across worktrees goes through the orchestrator.
- Mechanics go to `integration-orch`: `gate request <PR> <full sha>`, `merge request <PR> <full sha>`, preview and review launches. Judgment goes to the orchestrator: ROOT review, opening a PR, cross-worktree questions, blockers.
- An agent on another machine sends the same one-line prompt through `ssh -o BatchMode=yes <orchestrator host> "herdr agent prompt <agent> '<line>'"`; the host alias comes from your brief or machine setup, never from this skill.
- Only the orchestrator merges, from the merge packet.

## Gates and merge packets

- One gate on the final sha, not per commit. Push, run the repo's own checks in your terminal pane, then send `gate request <PR> <full sha>` with their results. A failure those checks would have caught is a lead miss.
- A pane command ends with a unique marker (`echo <MARKER>_RC=$?`); wait with `herdr pane wait-output`. Use `git --no-pager` in every pane command.
- On `merge request`, `integration-orch` writes a packet: PR, issue, head sha equal to the gated sha, merge-tree result, files shared with the base branch, gate counts, review and acceptance verdicts, `root=none|area|sensitive`, whether the DEC-023 handoff is posted, and `ready=yes|no`. A shared file or a sha changed after approval means integrate, re-gate and approve again.
- ROOT changes (contracts, schema, migrations, IAM, dependencies, MCP tool lists, plugin manifests, AGENTS.md) are written as a patch and sent to the orchestrator before the push. Ask before opening a PR. Never merge, publish or mutate infrastructure without that authorization.

## Closing a front (DEC-023)

No session stays open after its work is done. Before you stop, post an English handoff comment on your issue covering what was done (commits, PR, sha), verdicts and evidence paths, what is left with follow-up issue ids, decisions taken and why, and where your status file is. Then run `herdr agent prompt <parent> "<name>: DONE, handoff posted"`. The parent checks the comment and closes your pane. Ask the scribe to record any decision in Knowledge; do not write it there yourself unless asked.

## The orchestration-wake plugin

The `pai.orchestration-wake` Herdr plugin delivers the push half of DEC-029: it prompts a parent when a one-shot child finishes or blocks and a requester when a pane exits. It reads Herdr's semantic agent status, so it works for Claude and Codex panes. It never fails a launcher and logs its decisions in its state directory.

- Install it per machine, never over a live installation: `herdr plugin install pailat/pai-console-plugin/herdr-plugins/orchestration-wake --ref <tag>`.
- Launchers set pane tokens with the plugin's `pai-pane-meta <pane_id> role=… parent=… requester=… issue=… name=… wake_on_done=1` instead of `herdr pane report-metadata`, so the tokens survive a Herdr restart.
- Settings come from the environment, then `config.env` in the plugin state directory: `PAI_WAKE_FALLBACK`, `PAI_WAKE_OUTBOX`, `PAI_WAKE_HOSTS` (`alias=ssh-host[:remote-shell]` for remote targets). Local Herdr calls use `HERDR_BIN_PATH`.
- The plugin complements the rules above; it does not replace arming your own wait.
