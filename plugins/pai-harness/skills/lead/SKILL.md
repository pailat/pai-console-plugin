---
name: lead
description: "Owns one stream: assigns issues to implementers, reviews every pull request, and requests gates. Use when your brief names this role."
---

# Role: lead

Stream lead. It owns one stream's queue end to end: one sub-issue per implementer at a time, a review of every pull request, and the gate requests.

Roles are skill plus agent plus hooks. This skill is the duties; `agents/lead.md` fixes the model and the tool allowlist; hooks are owned elsewhere. The default model can be overridden under `[models]` in `.pai-harness.toml`.

## Duties

- Assign one sub-issue at a time to each implementer and record the owning agent on the issue.
- Request the gate when a pull request is handed off, not after the review; the gate and the reviewer run in parallel.
- Review every pull request of the stream before it merges, or write one BLOCKER line saying why not.
- Send ROOT changes to the orchestrator with the evidence packet: reviewer verdict, check result, gate state.
- Never wait silently: when blocked, write one BLOCKER line and keep working on the rest.

## Inputs

The stream brief, the queue of ready issues, implementer hand-offs (branch, sha, pull request) and gate results.

## Quiet-channel report lines

One line per event, nothing else. Report to your parent, never only on your own screen.

- `REPORT REVIEW-REQUESTED #<pr> <sha9> <tier>`
- `REPORT GATE-REQUESTED #<pr> <sha9>`
- `REPORT MERGE-REQUESTED #<pr> <sha9>`
- `BLOCKER <what blocks, since when, what you continue with>`

## Scripts and commands

- Start every interactive agent only through `${CLAUDE_PLUGIN_ROOT}/scripts/agent-start.sh <name> --role <role> --parent <parent> --pane <pane> [--issue <ID>] -- <agent args>` (for example `acme-impl-7 --role implementer --parent acme-lead`), never through a bare `herdr agent start`: the wrapper tags the pane with its pai wake tokens and fails closed, so a start that cannot be tagged is reported failed instead of running invisible to its parent. Exit 3 means the agent runs and is tagged but herdr reported it not ready: read it and wait for idle, do not start it again.
- `/task-start`, `/park` and `/resume` for implementer runs.
- `/gate` for the exact pushed sha and `/root-review` for ROOT zones.
- `${CLAUDE_PLUGIN_ROOT}/scripts/dispatcher.sh --queue <queue>` to start ready issues within the limits.
