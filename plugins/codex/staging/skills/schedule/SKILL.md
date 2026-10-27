---
name: schedule
description: "Plan and maintain Pai Console project schedules: milestones, dates, amounts, acceptance criteria, baseline, milestone/task dependencies, unified tasks, legacy Knowledge task compatibility, task board, and project closure/reopening. Use for work plans, schedules, milestones, tasks, kanban, dependencies, baselines, progress, delays, or closing/reopening projects."
argument-hint: "[project] [plan or update requested]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Schedule and tasks

Read shared `pai-console` first through the current client's skill mechanism.

## Model

- **Milestones** (`milestone_*`): planned/actual dates, acceptance criteria, billable amount in cents, `pending`/`in_progress`/`completed` status, owner, baseline.
- **Tasks:** use the unified `task_*` primitive in `../tasks/SKILL.md`, with project as primary context and milestone/product links as additional contexts. Legacy Knowledge task nodes remain compatible with older board/dependency responses; follow each returned transition rather than mixing their schemas. `timeline_get` computes `scheduleLabel` and `blockedNow` using today's date in `America/Mexico_City`. Literal labels are Pendiente, En curso, Atrasado, Completado, Cancelado; preserve these server values.
- **Dependencies:** milestone `milestone_dependency_*` (finish-to-start with `reason`, `visibility`) and task `task_dependency_*`. Both reject duplicates/cycles. Change one with `milestone_dependency_update {id, reason, visibility}` or `task_dependency_update {id, reason, visibility}`: both fields are required, so resend the current value of the one you keep (from timeline_get). Remove one with `milestone_dependency_delete {dependencyId}` or `task_dependency_delete {id}`; it is a hard delete (recreate with `_create`), so confirm first, especially for a `client` dependency the client can see. Unknown ids are `NOT_FOUND`. These writes are staff-only.
- **One milestone:** `milestone_get {id}` returns acceptance criteria, planned/baseline/actual dates, owner, amount and payment status; clients get it without staff ids. Read it before changing or completing a milestone.
- **Board:** `task_board {milestoneId?, search?, columns?, limit, offset}`, paginated by `nextOffset`.

The following columns describe the legacy Knowledge board, not unified task status enums:

| Column | Legacy task state |
|---|---|
| Backlog (`backlog`) | `draft` or `proposed` |
| To do (`todo`) | `active` |
| Done (`done`) | Resolved `done` |
| Discarded (`discarded`) | Resolved `wont_do` or rejected |

Each task has `revision`, `citation`, and exact permitted transitions in `moves`, with tool/input. Follow them.

## Plan from scratch

1. Read `timeline_get`, `milestone_list`, `task_board`. Adjust existing plans; never duplicate.
2. `milestone_owner_options` provides valid `ownerUserId` values.
3. Create milestones in order through `milestone_create`:
   - Spanish business `name`, `description`, `acceptanceCriteria` defining completion;
   - `startDate`, `endDate`: `YYYY-MM-DD` for a day, or an ISO date-time with offset plus `startHasTime`/`endHasTime: true` for an agreed time (shown in `America/Mexico_City`). Precision is never inferred from the string; a date-only value keeps its legacy UTC day;
   - optional `estimatedMinutes` (null unknown, 0 explicit zero), only when the user gives an estimate;
   - **Cents** `amount`, **explicit** `currency` (`mxn`/`usd`): defaults to `usd` whereas proposals default to `mxn`; make the choice explicit;
   - explicit `sequence` (1, 2, 3…); absent sequence uses max+1 and can conflict with concurrent writes.
4. `milestone_dependency_create {predecessorMilestoneId, successorMilestoneId, reason, visibility}`. Explain waiting in `reason`; `visibility` is `internal`/`client`, client-visible when `client`.
5. Use `../tasks/SKILL.md`: task_create with title, contexts beginning with {kind:"project",id}, and the milestone/product as additional contexts. Search first, keep the agreed dates/assignee and distinguish proposed draft from active work. The older Knowledge task route remains compatible; `examples/task.json` documents that legacy path, not the unified task input.
6. `task_dependency_create {predecessorTaskId, successorTaskId, reason, visibility}`; default `visibility: internal`; use canonical IDs accepted by the returned dependency input; do not substitute a task shortId or invent a Knowledge node.
7. Once the user confirms the client agreed to the plan, `milestone_baseline_capture` per milestone. **One capture, immutable:** request explicit confirmation.

## Daily updates

| Event | Action |
|---|---|
| Milestone starts | `milestone_update {status:"in_progress", actualStartDate}` |
| Milestone finishes | `milestone_update {status:"completed", actualEndDate}` after confirming `acceptanceCriteria` |
| Backlog ↔ To do | `task_get` → `task_update {taskId,expectedRevision,status:"todo"}` or draft; a person confirms proposals |
| Task completes | `task_complete {taskId,expectedRevision,closeNote}` |
| Task discarded | `task_cancel {taskId,expectedRevision,closeNote}` |
| Task dates change | `task_get` → `task_update` with expectedRevision and changed startAt/startHasTime/dueAt/dueHasTime |
| Milestone dates change | `milestone_update` with the changed date and its `*HasTime` flag (`actualStartHasTime`/`actualEndHasTime` for actual dates); an omitted flag keeps the stored precision and clearing a date resets it. Order errors: `END_BEFORE_START`, `MIXED_PRECISION_SAME_DAY` (timed and date-only on the same day: use one precision), `LEGACY_TIMESTAMP_ORDER` (stored values out of order: fix both ends together) |
| Reorder milestones | `milestone_reorder {items:[{id, sequence}]}` silently ignores out-of-project IDs; verify `milestone_list` |

- Closed tasks cannot reopen; create/link a new task if needed.
- A person rejects proposed tasks in the board.
- Never manually edit milestone **`paymentStatus`**: payments recalculate it (`proposals-payments`) and overwrite manual values.

## Status reporting

1. Read `timeline_get` (milestones, dependencies, `scheduleLabel`, `blockedNow`) and `task_board`.
2. Summarize milestone states, overdue/blocked tasks, upcoming due dates. CLI clients need text fallback; never claim a widget rendered without evidence (`pai-console` §6).
3. If requested, `status_update_publish {health, headline, body}`: `health` `on_track`/`at_risk`/`off_track`, `headline` ≤120, `body` ≤600. **Immediately client-visible:** show the text before publication.

## Close/reopen a project (staff)

1. `project_close_review`: pending `openTasks`, `unresolved` (questions, assumptions, risks), `pendingSuggestions`, `counts`, each with a closing `action` such as task `knowledge_resolve` `done`/`wont_do`. Nonblocking: show the review and resolve only what the user decides.
2. `project_close {status: "completed" | "cancelled", summary?}` (≤4000) makes the project **read-only**. Returns `merged[]`; touched products record `knowledge_merged`. `project_update` with `completed`/`cancelled` also closes. Confirm beforehand.
3. On closure, **all content writes** (Knowledge, including product Knowledge through that project; pages, notes, folders, files, comments) return `CONFLICT` without `cause`, with literal server text “El proyecto está cerrado y es de solo lectura. Un miembro del equipo de Pai puede reabrirlo.” This is not stale CAS: never reread/retry. Reads, proposals, payments, milestones, status updates, product links remain available. `project_summary` returns `project.readOnly: true`.
4. `project_reopen {status?: "draft" | "planned" | "active" | "on_hold"}` (default `active`) **only when requested**; audited. Clients cannot close/reopen.

Spanish status/error quotations above intentionally preserve server contracts. Replies follow the user's language; retain Mexican business formatting and cents/MXN conventions.

## Avoid

- Never delete milestones with payments/CFDI (`milestone_delete` orphans them); ask how to handle their billing.
- Never capture baseline without explicit confirmation.
- Never close/reopen on your own or retry a closed-project write.
- Never use another kind for tasks or represent goals/decisions as tasks.
- Never send whole pesos/dollars: amounts are cents (`150000` = 1 500.00).
