---
name: crm
description: "Pai Console CRM for staff or Console roles with crm:access through corp MCP: leads, qualification, workspaces, opportunities, forecasting, submission-to-project traceability, and CRM tasks. Use for Forms submissions, duplicate-safe lead creation/import, contacting/qualifying/disqualifying prospects, Discovery workspaces, pipeline stages, holds/wins/losses, contacts/probability, attention queues, or task details, priorities, tags, scheduling, assignment, and completion."
argument-hint: "[lead, opportunity, or organization]"
compatibility: "Pai 0.2.5+ (MCP corp, crm:* permissions)"
---

# Pai CRM

Read shared `pai-console` first through the current client's skill mechanism. CRM belongs to the Pai team on corp MCP: staff and Console roles with `crm:access`; non-staff receive **only CRM tools**. Clients never see CRM; the public edge does not register these tools. CRM tools work by lead/opportunity ID, not project `organizationId`/`projectId`.

Full inventory: `../pai-console/references/tools.md`, CRM section. Respond in the user's language; preserve Mexican Spanish business formatting, separate MXN/USD amounts, and `America/Mexico_City` dates. Spanish server messages/UI labels and existing identifiers below are intentional literal exceptions.

## Permissions first

`crm_access_get` (no arguments) returns capabilities; empty list means no access.

| Permission | Capability |
|---|---|
| `crm:access` | Overview, leads, submissions, records |
| `crm:edit` | Create/move leads, opportunities, tasks, contacts; add notes |
| `crm:convert` | Win (`crm_opportunity_win`) |
| `crm:revenue` | Amounts, weighted forecast, `crm_opportunity_list`, `crm_opportunity_event_list`, probability changes |
| `crm:purge` | Purge chain-free junk (`crm_lead_purge`) |
| `crm:import` | Historical CRM import (`crm_lead_import`) |
| `crm:join` | Enter client organizations via `crm_lead_workspace_join` (absent without it), `link_existing`, become admin of lead-created organization; opens projects/proposals/payments/resources outside CRM |

All permissions also require `crm:access`. **Roles group permissions; guards check permissions, not role names.**

| Role | Permissions |
|---|---|
| `crm.viewer` | `crm:access` |
| `crm.sales` | `crm:access`, `crm:edit` |
| `crm.closer` | `crm:access`, `crm:edit`, `crm:convert`, `crm:revenue` |
| `crm.admin` | All except `crm:join` |

- Custom roles may include any permission, including `crm:join`.
- Until Administration appears in the permission catalog, platform admins have all permissions.
- Impersonated sessions have none.
- **Visibility is not owner-scoped:** `crm:access` sees all leads/opportunities/tasks; `owner: "me"` is a filter, not a permission.
- Organization staff without Pai staff status use their real CRM role; organization staff status alone grants no CRM.
- Without `crm:revenue`, amounts are absent even from history: never invent/estimate them.

**CRM-only users:** start with `crm_access_get`, `crm_overview_get`. No `organization_list`, projects, proposals, Knowledge, or Resources. Staff must handle dependencies such as linking a sent proposal for `proposal_sent` or accessing Discovery projects. Explain this; never bypass.

### Without `crm:join`

- `link_existing` in `crm_lead_workspace_open`, `crm_lead_qualify`, `crm_lead_import` yields `FORBIDDEN`: “No tienes permiso para ligar el lead a una organización existente: crea la organización desde el lead”. If the organization **already exists**, never duplicate it with `create_from_lead`; stop and ask someone with `crm:join` to link it or grant permission. `create_from_lead` is only for accounts absent from Pai.
- `create_from_lead` creates an organization but **does not make you a member**.
- `crm_opportunity_create` only opens opportunities for CRM-managed organizations with a lead/opportunity.
- Never enter an organization through an alternative route.

## Server invariants

- **Every open record needs a next step:** open leads (`new`, `contacted`) and opportunities require a dated task with dependency `{body, dueAt, waitingOn, type?, detail?, priority?, tags?}`; `waitingOn` is `pai` or `client`. Creation requires `firstTask`/`task`; stage changes or completion of the last task require `nextTask`. Agree tasks/dates with the user, never invent dates.
- **`dueAt` uses CDMX (`-06:00`).** Without a specified time, business-day end `T18:00:00-06:00`, displayed as “Sin hora” (all-day). With a time, use it, e.g. `T10:30:00-06:00`. Never use midnight/noon UTC to mean a day; those appear as timed events.
- **CAS:** every lead/opportunity write carries `expectedRevision` from `crm_lead_get`, `crm_lead_record`, or `crm_opportunity_get`. On `CONFLICT`, reread and reconsider; shared retry limit applies.
- **Cents** (`4200000` = $42,000.00) by currency (`mxn`, `usd`). **Never sum MXN and USD**; report separately.
- Archive is reversible through `*_unarchive`; only `crm_lead_purge` deletes chain-free junk.
- All changes enter `crm_lead_event_list`/`crm_opportunity_event_list` as MCP actions.
- **Use staff names** supplied by tools (actor/owner/qualifier), never seek/write staff email. Client lead/contact emails remain CRM data.

## Read the situation

| Question | Tool |
|---|---|
| CRM status | `crm_overview_get {from?, to?}`: figures, 90-day funnel, attention queue, daily tasks, conversions. `period` compares `from`–`to` (`YYYY-MM-DD`, CDMX days, default 30, max 366) with equal prior period: created/won/lost leads/opportunities, close rate, median first contact, completed tasks, origin/funnel. Daily ≤31 days, weekly ≤180, otherwise monthly. `ownerLoad`: each owner's current open load |
| My tasks | `crm_task_list`: default own open tasks, most overdue first, window counts |
| Needs attention | `crm_lead_list {waitingOn: "attention", owner: "me"}`, `crm_opportunity_list {waitingOn: "attention", owner: "me"}`: overdue, no next step, or waiting on Pai today |
| Lead metrics | `crm_lead_summary`: own attention queue, median first-contact response, new outside 1-business-hour SLA, open without next step |
| Forecast | `crm_opportunity_summary`: weighted/unweighted per currency, 90-day close rate, held opportunities |
| Full lead | `crm_lead_record`: qualification, submission, workspace, opportunities, seeded nodes, activities |
| Full opportunity | `crm_opportunity_get`: contacts, proposals/versions, activities, history |
| Origin/outcome chain | `crm_trace_get {opportunityId, asOf?}`: submission → lead → workspace → opportunity → proposal → project → milestones → product |
| Valid owners | `crm_owner_list`: users with `crm:edit`, including CRM-only; select `ownerUserId`/`deliveryLeadUserId` from here, never invent IDs |

`crm_lead_list` filters: `query`, `source`, `owner` (`me`, `none`, ID), `period` (`30d`, `90d`, `year`, `all`; omitted means all), `waitingOn` (`attention`, `pai`, `client`, `overdue`, `none`, `outsideSla` for overdue first contact excluding imports), `archived: "1"`. Opportunities accept the same `waitingOn` except `outsideSla`, plus `serviceLine`, `offering`, `kind`, `currency`, `market` (`mx`, `br`), `closeWindow` (`overdue`, `30d`, `90d`), `organizationId`.

For visuals use `views` (`Stats`, `Kanban`, `DataTable`, `BarList`), `view_render`, and as-of date. CLI requires text fallback; never claim a widget rendered without evidence.

## Leads

Stages: `new` → `contacted` → `qualified` (or `unqualified`) → `converted` (organization's first win). Immutable sources: `form`, `onboarding`, `manual`, `referral`, `mcp`, `import` (`crm_lead_import`).

### Create

1. **Forms submission:** `crm_submission_get` → `crm_lead_create_from_submission {submissionId, ownerUserId, firstTask}`. Use submission data unchanged. Junk submission without lead: `crm_submission_spam` archives it.
2. **Referral/manual/MCP:** if email exists, first `crm_lead_duplicates {email}` for same email/domain and client organizations. Otherwise search name/company with `crm_lead_list {query}`. Show matches and decide with user. Then `crm_lead_create {fullName, ownerUserId, firstTask, email?, phone?, company?, role?, source?, referredBy?, need?}` requires **email, phone, or company**. Emails owner, or `crm:edit` team if no owner.
3. **Historical CRM migration:** `crm_lead_import`, permission `crm:import`, one record/call in its **actual** stage including won/lost, original `createdAt`/`firstContactedAt`, and available `workspace`, `opportunity`, `notes`, `tasks`. `externalRef` (source ID) plus `externalSystem` make it idempotent: repeat returns `created: false`. With opportunity, lead is `qualified` (`converted` if won), and `workspace` required. Preserve full source text in `notes`. Never use for a new lead.

### Notes

`crm_lead_note_add {id, body}`, `crm_opportunity_note_add {id, body}` (≤20 000 characters) append dated/attributed history. **Immutable**: corrections are new notes. They do not change stage, next step, or last contact. Record contact through `crm_lead_update {stage: "contacted"}` or task completion.

### Move

| Step | Tool | Requirement/effect |
|---|---|---|
| Contacted | `crm_lead_update {stage: "contacted", nextTask}` | Sets first contact, completes open task |
| Data/owner edit | `crm_lead_update` | CAS |
| Tasks | `crm_task_create {record: {kind: "lead", id}, task}`, `crm_task_complete {taskId, nextTask?}`; aliases `crm_lead_task_create`, `crm_lead_task_complete` | Last open task requires `nextTask` |
| **Qualify** | `crm_lead_qualify {qualification, workspace?, opportunity}` | `contacted` lead, all four criteria, workspace |
| Disqualify | `crm_lead_disqualify {reason, note?, closeOpenTask?}` | `new`/`contacted`; `other` needs `note` |
| Duplicate | `crm_lead_mark_duplicate {duplicateOfLeadId}` | Survivor cannot itself be duplicate |
| Archive/restore | `crm_lead_archive`, `crm_lead_unarchive` | Reversible |

**Four qualification criteria:** `need`, `budgetRange` (`lt150`, `150-300`, `300-600`, `gt600` in thousands of MXN, or `unknown`), `timeline`, `decisionMaker`. Qualification seeds Forms Knowledge and creates **first Discovery opportunity (10%)** with task. Ask for missing criteria, never fabricate.

```json
{ "leadId": "…", "expectedRevision": 3,
  "qualification": { "need": "Recurring collection with Stripe Billing", "budgetRange": "150-300", "timeline": "Start in November", "decisionMaker": "Finance Director" },
  "workspace": { "mode": "create_from_lead" },
  "opportunity": { "title": "Subscription billing", "serviceLine": "stripe", "currency": "mxn", "amountMin": 15000000, "amountMax": 30000000, "expectedCloseAt": "2026-11-30",
    "task": { "body": "Send Discovery scope", "dueAt": "2026-10-15T18:00:00-06:00", "waitingOn": "pai" } } }
```

`workspace`: `{mode: "create_from_lead", organizationName?}` or `{mode: "link_existing", organizationId}`; omit if already assigned.

Disqualification reasons: `not_a_fit`, `no_budget`, `no_response`, `timing`, `competitor`, `other`. Spam is archived/purged, not disqualified; duplicates are linked. Qualified leads cannot be disqualified.

### Workspace (organization + project)

1. `crm_lead_organization_suggestions {leadId, query?}`: similar domain/member/name organizations or query matches, with origin (`self_service`, `client`, `prospect`) and fields to fill. **Never auto-links.**
2. Confirm new versus existing with user.
3. `crm_lead_workspace_open {workspace}` (or in qualification) creates/links organization, fills only empty fields, opens draft Discovery project (literal title “Descubrimiento”). **Cannot relink later.** Existing links require `crm:join`.
4. Linking grants no membership; use audited `crm_lead_workspace_join` (“Entrar como staff”), permission `crm:join`.

### Purge

`crm_lead_purge {reason: spam|test|mistake}` **irreversibly** hard-deletes a **chain-free** lead (no organization/project/opportunities/nodes/duplicates), tasks, and history. Archive chained records. Always confirm, including staging/develop.

## Tasks

Tasks belong to open leads (`new`, `contacted`), open/held opportunities, or accounts (`record.kind: "account"`, `record.id` = `organizationId`).

| `state` | Board column | Source |
|---|---|---|
| `todo` | To do | Open, not started |
| `in_progress` | In progress | `crm_task_update {progress: "in_progress"}`; `progress: "todo"` reverses |
| `waiting` | Waiting for client | `waitingOn: "client"` |
| `done` | Done | `crm_task_complete` |

### Read

- `crm_task_list`: defaults to own open tasks, most overdue first; `counts` by `overdue`, `today`, `week`, `later` in CDMX.
  - Filters: `owner` (`me`, `all`, `crm_owner_list` ID), `status` (`open`, `done`), `subject` (`lead`, `opportunity`, `account`), `due`, `priority`, `tag`, `query` matching task/record text.
- `crm_task_get {taskId}`: `body` title, `type`, Markdown/null `detail`, nullable `priority`, `tags`, `dueAt`, `waitingOn`, board `state`, `startedAt`, `doneAt`, open-only `window` (overdue/today/week/later), `owner`, `record` (`kind`, `id`, `title`, `company`), `createdAt`. List returns same per-task shape plus `counts` and `truncated`; narrow filters if truncated.
- **Check `crm_task_tag_list` before inventing tags**; ordered by team usage.

### Create

`crm_task_create {record: {kind, id}, task, ownerUserId?}`; owner defaults to record owner or self.

| Field | Content |
|---|---|
| `body` | **Short title ≤500**, e.g. send NDA or scope call; detail belongs elsewhere |
| `dueAt` | Agreed future CDMX date; without time `2026-10-15T18:00:00-06:00` (“Sin hora”), otherwise actual time such as `2026-10-15T10:30:00-06:00`; never invent |
| `waitingOn` | `pai` or `client` |
| `type` | `todo` default, `call`, `email`, `meeting` |
| `priority` | `low`, `medium`, `high`; omitted means no priority |
| `tags` | ≤10, ≤40 characters each; reuse team tags |
| `detail` | Markdown notes/context/steps, ≤20 000 |

Same shape for `firstTask`, `task`, `nextTask` across CRM tools.

Write `detail` for Console's task page/editor: one or two context sentences explaining cause/trigger, checklist (`- [ ] …`) for multiple steps, Markdown links and concrete names/dates. No top-level `#` (title is `body`), no unnecessary sensitive data.

```json
{ "record": { "kind": "opportunity", "id": "…" },
  "task": { "body": "Send Discovery scope", "dueAt": "2026-10-16T18:00:00-06:00", "waitingOn": "pai", "type": "email", "priority": "high", "tags": ["proposal"],
    "detail": "Mariana requested the scope before Friday's committee.\n\n- [ ] Adjust the SOW for both Stripe integrations\n- [ ] Validate amounts with Finance\n- [ ] Send to mariana@cliente.mx, copying Luis" } }
```

### Change

`crm_task_update {taskId, …}` updates **open** tasks: future `dueAt`, `ownerUserId` from `crm_owner_list`, `waitingOn`, `type`, nullable `priority` to clear, `progress`, **complete** `tags` list (`[]` clears), `detail` (`null`/empty clears).

**New `body` creates a corrected task under a new returned ID and archives the old task**, rather than editing it. Use the new ID thereafter. All changes enter history; nothing is deleted.

### Complete

`crm_task_complete {taskId, nextTask?}` marks done. Last open task of an open lead/opportunity **requires `nextTask`**, created on same record; agree it with user. Returns completed task and `next`.

## Opportunities

Open stages/probabilities: `discovery` 10% → `scoping` 25% → `proposal_sent` 50% → `negotiation` 75%; `won` 100%, `lost` 0%. `on_hold` excluded from forecast.

`kind`: `new_business` requires qualified account `leadId`, opens project; `expansion` opens project; `renewal`/`change_order` derive from won `parentOpportunityId`, reuse its project.

`offerings` must belong to `serviceLine`:
- `stripe`: billing, connect, payments, checkout, invoicing, tax, terminal, radar, identity
- `product_design`: app, dashboard, website
- `ai`: mcp_connector, ai_app, implementation_plan

Commercial model: `fixed_price`, `time_and_materials`, `retainer`.

`market`: `mx` (Mexico), `br` (Brazil), or unknown `null`; **not currency** (Brazil can quote USD). Set on create/`crm_opportunity_update`, `null` clears; filter `crm_opportunity_list {market}`. `discoveryPaid` indicates paid Discovery.

### Create

`crm_organization_list {query}` → `crm_organization_get {organizationId}` (qualified leads, Portal people, open/won opportunities) → `crm_opportunity_create {organizationId, kind, title, serviceLine, offerings, currency, amountMin, amountMax, expectedCloseAt, market?, discoveryPaid?, task, …}`. Title cannot duplicate another open opportunity in that organization.

### Move

| Step | Tool | Requirement |
|---|---|---|
| Stage/data | `crm_opportunity_update {stage, nextTask, …}` | Stage change needs `nextTask`; `proposal_sent` needs linked **sent** `proposalId` (`proposals-payments`) |
| Hold | `crm_opportunity_hold {task}` | Resume date in `task.dueAt`; resume with `update` and open stage |
| Lose | `crm_opportunity_lose {reason, note?, competitorName?}` | price, timing, no_budget, competitor, no_response, no_decision, in_house, not_a_fit, other; `other` requires `note` |
| Probability | `crm_opportunity_probability {probability, reason}` or `{reset: true}` | `crm:revenue`; stage change resets to stage probability |
| Contacts | `crm_opportunity_contact_add {leadId \| userId, role, isPrimary?}`, `_primary`, `_remove` | decision_maker, champion, finance, technical, user, other |
| Archive/restore | `crm_opportunity_archive`, `crm_opportunity_unarchive` | Reversible |

### Win

`crm_opportunity_win` is **IRREVERSIBLE**, requires `crm:convert`. Gather and confirm:

1. `acceptedProposalVersionId`: project proposal `send`/`accept` version from `crm_opportunity_get`. Sent proposals become accepted under `acceptedByName` or the deciding person.
2. `deliveryLeadUserId` from `crm_owner_list`, `startAt` (`YYYY-MM-DD`), `serviceLine`, ≥1 offering.
3. A **`decision_maker`** contact.

First organization win converts its lead and activates account; project becomes planned and a handoff-debrief resource is created (literal title “Debrief de traspaso”). **No Knowledge/pages are copied.** Continue with `schedule` and `proposals-payments`.

## Common mistakes

- Task detail in `body`, invented tags without reading tag list, old ID after title correction, partial `tags` replacing the full list.
- Lead creation without duplicate search; historical import for new leads or changed `externalRef` on reimport.
- Treating notes as contact/stage changes; missing/stale `expectedRevision`.
- Summing currencies, revealing/estimating amounts without `crm:revenue`, inventing probabilities.
- Disqualifying spam instead of archive/purge.
- Unconfirmed workspace linking or `link_existing` without `crm:join`.
- Winning without decision maker and sent/accepted proposal version.
