---
name: crm
description: "Pai Console CRM for users with effective granular CRM permissions through corp MCP: leads, qualification, workspaces, opportunities, forecasting, submission-to-project traceability, and CRM tasks. Use for Forms submissions, duplicate-safe lead creation/import, contacting/qualifying/disqualifying prospects, Discovery workspaces, pipeline stages, holds/wins/losses, contacts/probability, attention queues, or task details, priorities, tags, scheduling, assignment, and completion."
argument-hint: "[lead, opportunity, or organization]"
compatibility: "Pai 0.2.5+ (MCP corp, granular IAM permissions)"
---

# Pai CRM

Read shared `pai-console` first through the current client's skill mechanism. CRM belongs to the Pai team on corp MCP: users with effective `crm.*` IAM grants; CRM-only users can also receive the unified `task_*` tools their task grants allow. Clients never see CRM; the public edge does not register these tools. CRM tools work by lead/opportunity ID, not project `organizationId`/`projectId`.

Full inventory: `../pai-console/references/tools.md`, tool index. Respond in the user's language; preserve Mexican Spanish business formatting, separate MXN/USD amounts, and `America/Mexico_City` dates. Spanish server messages/UI labels and existing identifiers below are intentional literal exceptions.

## Permissions first

`crm_access_get {}` reports the person's effective catalog permissions. Discovery is permission-scoped; use `../iam/SKILL.md` for access diagnosis and never infer a grant from a role name or platform role.

| Permission examples | Capability |
|---|---|
| crm.leads.list / crm.leads.get / crm.leads.create / crm.leads.update | Separate lead read/create/edit actions |
| crm.opportunities.win | Win an opportunity |
| crm.opportunityAmounts.get | Read amounts; absent amounts must not be estimated |
| crm.leads.purge | Chain-free junk purge or explicitly requested ARCO anonymization |
| crm.imports.create | Historical import |
| iam.staffAssignments.create | Enter/link a client organization through the authorized CRM workspace flow |
| crm.tasks.list / get / create / update / complete | Independent CRM task grants; reschedule, assign, setPriority and setTags are also separately checked |

Actual permission identifiers include the full service.resource.verb string; consult the generated inventory or iam_permission_catalog for each operation. The retired colon-style permissions are not current grants. Platform admins use stored IAM bindings and remain subject to denials and boundaries. Impersonated sessions have no CRM grants. Organization staff status alone grants no CRM access. Owner filters select data; they do not replace authorization.

**CRM-only users:** start with crm_access_get and the overview/record tools actually exposed. Do not assume organization_list, projects, proposals or Resources are available. Explain missing cross-domain access rather than changing roles or memberships.

### Without `iam.staffAssignments.create`

- `link_existing` in `crm_lead_workspace_open`, `crm_lead_qualify`, `crm_lead_import` yields `FORBIDDEN`: “No tienes permiso para ligar el lead a una organización existente: crea la organización desde el lead”. If the organization **already exists**, never duplicate it with `create_from_lead`; stop and ask someone with `iam.staffAssignments.create` to link it or grant permission. `create_from_lead` is only for accounts absent from Pai.
- `create_from_lead` creates an organization but **does not make you a member**.
- `crm_opportunity_create` only opens opportunities for CRM-managed organizations with a lead/opportunity.
- Never enter an organization through an alternative route.

## Server invariants

- **Every open record needs a next step:** open leads (`new`, `contacted`) and opportunities require a dated task with dependency `{body, dueAt, waitingOn, type?, detail?, priority?, tags?}`; `waitingOn` is `pai` or `client`. Creation requires `firstTask`/`task`; stage changes use `nextTask`; unified completion of the last task uses `next` with `title`. Agree tasks/dates with the user, never invent dates.
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
| My tasks | `task_list {section:"crm",assignee:"me"}`: filtered unified tasks, window counts |
| Needs attention | `crm_lead_list {waitingOn: "attention", owner: "me"}`, `crm_opportunity_list {waitingOn: "attention", owner: "me"}`: overdue, no next step, or waiting on Pai today |
| Lead metrics | `crm_lead_summary`: own attention queue, median first-contact response, new outside 1-business-hour SLA, open without next step |
| Forecast | `crm_opportunity_summary`: weighted/unweighted per currency, 90-day close rate, held opportunities |
| Full lead | `crm_lead_record`: qualification, submission, workspace, opportunities, seeded nodes, activities |
| Full opportunity | `crm_opportunity_get`: contacts, proposals/versions, activities, history |
| Origin/outcome chain | `crm_trace_get {opportunityId, asOf?}`: submission → lead → workspace → opportunity → proposal → project → milestones → product |
| Valid owners | `crm_owner_list`: users with the required create/edit grants, including CRM-only; select `ownerUserId`/`deliveryLeadUserId` from here, never invent IDs |

`crm_lead_list` filters: `query`, `source`, `owner` (`me`, `none`, ID), `period` (`30d`, `90d`, `year`, `all`; omitted means all), `waitingOn` (`attention`, `pai`, `client`, `overdue`, `none`, `outsideSla` for overdue first contact excluding imports), `archived: "1"`. Opportunities accept the same `waitingOn` except `outsideSla`, plus `serviceLine`, `offering`, `kind`, `currency`, `market` (`mx`, `br`), `closeWindow` (`overdue`, `30d`, `90d`), `organizationId`.

For visuals use `views` (`Stats`, `Kanban`, `DataTable`, `BarList`), `view_render`, and as-of date. CLI requires text fallback; never claim a widget rendered without evidence.

## Leads

Stages: `new` → `contacted` → `qualified` (or `unqualified`) → `converted` (organization's first win). Immutable sources: `form`, `onboarding`, `manual`, `referral`, `mcp`, `import` (`crm_lead_import`).

### Create

1. **Forms submission:** `crm_submission_get` → `crm_lead_create_from_submission {submissionId, ownerUserId, firstTask}`. Use submission data unchanged. Junk submission without lead: `crm_submission_spam` archives it.
2. **Referral/manual/MCP:** if email exists, first `crm_lead_duplicates {email}` for same email/domain and client organizations. Otherwise search name/company with `crm_lead_list {query}`. Show matches and decide with user. Then `crm_lead_create {fullName, ownerUserId, firstTask, email?, phone?, company?, role?, source?, referredBy?, need?}` requires **email, phone, or company**. Emails owner, or the permitted CRM team if no owner.
3. **Historical CRM migration:** `crm_lead_import`, permission `crm.imports.create`, one record/call in its **actual** stage including won/lost, original `createdAt`/`firstContactedAt`, and available `workspace`, `opportunity`, `notes`, `tasks`. `externalRef` (source ID) plus `externalSystem` make it idempotent: repeat returns `created: false`. With opportunity, lead is `qualified` (`converted` if won), and `workspace` required. Preserve full source text in `notes`. Never use for a new lead.

### Notes

`crm_lead_note_add {id, body}`, `crm_opportunity_note_add {id, body}` (≤20 000 characters) append dated/attributed history. **Immutable**: corrections are new notes. They do not change stage, next step, or last contact. Record contact through `crm_lead_update {stage: "contacted"}` or task completion.

### Move

| Step | Tool | Requirement/effect |
|---|---|---|
| Contacted | `crm_lead_update {stage: "contacted", nextTask}` | Sets first contact, completes open task |
| Data/owner edit | `crm_lead_update` | CAS |
| Tasks | `task_create {title,contexts:[{kind:"crm_lead",id}],dueAt,…}`, `task_complete {taskId,expectedRevision,next?}` | Last open task completion requires `next` |
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
3. `crm_lead_workspace_open {workspace}` (or in qualification) creates/links organization, fills only empty fields, opens draft Discovery project (literal title “Descubrimiento”). **Cannot relink later.** Existing links require `iam.staffAssignments.create`.
4. Linking grants no membership; use audited `crm_lead_workspace_join` (“Entrar como staff”), permission `iam.staffAssignments.create`.

### Purge

`crm_lead_purge {reason: spam|test|mistake}` **irreversibly** hard-deletes a **chain-free** lead (no organization/project/opportunities/nodes/duplicates), tasks, and history. Archive chained records. Always confirm, including staging/develop.

## Tasks

Use `../tasks/SKILL.md` for the unified primitive. The eight legacy CRM task aliases were removed from MCP; do not invoke them. Find CRM work with task_list {section:"crm",context:{kind:"crm_lead"|"crm_opportunity"|"crm_account",id}} and read task_get before writing.

Create with top-level title and contexts, not a nested task envelope. task_update edits open tasks in place with expectedRevision; task_complete uses next (title and future dueAt) for the last open step; task_cancel cannot leave an open lead/opportunity without a next step. Tags come from task_tag_list {section:"crm"}. CRM task access uses crm.tasks.* independently from project task access. CRM tasks archive/restore with their record.

CRM lead/opportunity creation and stage-change contracts still use nested firstTask/task/nextTask objects with body, dueAt and waitingOn. Do not replace their body with title: inspect the particular schema. The unified task_create/task_complete endpoints instead use title and next. Preserve this distinction in historical imports and qualification flows.

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
| Lose | `crm_opportunity_lose {reason, note?, competitorName?}` | price, timing, no_budget, competitor, no_response, no_decision, in_house, not_a_fit, other; `other` requires `note`; closes the open task; read the result (**Lose**) |
| Probability | `crm_opportunity_probability {probability, reason}` or `{reset: true}` | `crm.opportunityAmounts.get`; stage change resets to stage probability |
| Contacts | `crm_opportunity_contact_add {leadId \| userId, role, isPrimary?}`, `_primary`, `_remove` | decision_maker, champion, finance, technical, user, other |
| Archive/restore | `crm_opportunity_archive`, `crm_opportunity_unarchive` | Reversible |

### Lose

`crm_opportunity_lose` returns `{ opportunity, discovery }`, not the bare opportunity. `discovery` is `{ outcome, projectId?, reasons }`: what losing did to the deal's Discovery project.

| `outcome` | Meaning | What to do |
|---|---|---|
| `cancelled` | The project belonged to this deal alone and had nothing committed: it is cancelled and read-only (`projectId`) | Tell the user. Reopen only on request, with `project_reopen` (`schedule`) |
| `kept` | The project stays open; `reasons` (at least one) says why | Say the project continues and why. The loss is already recorded: **never retry it** or close the project another way |
| `none` | The deal has no project (no `projectId`, empty `reasons`) | Nothing to report about a project |

`kept` reasons: `not_draft` (no longer a draft), `shared_with_opportunity` (another deal that is not lost uses it), `proposal_sent`, `payment` (recorded, not voided), `milestone_active` (in progress or completed), `product_linked`, `open_tasks`, `client_activity` (a client member wrote in it), and `close_not_permitted`: nothing else keeps it, but whoever lost the deal lacks `resourcemanager.projects.close` on the project. With `close_not_permitted`, say the Discovery project was kept for that reason; someone holding that permission may close it if the user asks. Never infer the outcome from the opportunity alone.

### Win

`crm_opportunity_win` is **IRREVERSIBLE**, requires `crm.opportunities.win`. Gather and confirm:

1. `acceptedProposalVersionId`: project proposal `send`/`accept` version from `crm_opportunity_get`. Sent proposals become accepted under `acceptedByName` or the deciding person.
2. `deliveryLeadUserId` from `crm_owner_list`, `startAt` (`YYYY-MM-DD`), `serviceLine`, ≥1 offering.
3. A **`decision_maker`** contact.

First organization win converts its lead and activates account; project becomes planned and a handoff-debrief resource is created (literal title “Debrief de traspaso”). **No Knowledge/pages are copied.** Continue with `schedule` and `proposals-payments`.

## Privacy and organization accounts

- crm_lead_anonymize {leadId,expectedRevision,reason:"arco_request",requestedAt} irreversibly removes personal/free-text data from the lead, notes, history, seeded Knowledge and associated Forms answers/browser data while retaining IDs, stages, dates and metrics. Read the lead, verify the user's ARCO request/date and explicitly confirm the affected data. This is distinct from purging junk.
- crm_submission_anonymize {submissionId,reason:"arco_request",requestedAt} handles an archived Forms submission without a lead; if it has a lead, use lead anonymization for both. Never fabricate a request or run anonymization as routine cleanup.
- organization_domain_set {organizationId,domain} sets a lowercase unique business email domain without protocol/path; null clears it. Free-mail providers are rejected. It only improves organization suggestions, never auto-links a lead. crm_organization_list supports the prospect filter.
- Current lead creation/update/qualification/import inputs have refined limits and shapes. Read the exact snapshot schemas before sending free-form fields; do not truncate authentic input silently.

## Common mistakes

- Confusing unified task `title`/`detail` with nested CRM next-step `body`, inventing tags without reading the tag list, or using a stale revision; tags replaces the full list.
- Lead creation without duplicate search; historical import for new leads or changed `externalRef` on reimport.
- Treating notes as contact/stage changes; missing/stale `expectedRevision`.
- Summing currencies, revealing/estimating amounts without `crm.opportunityAmounts.get`, inventing probabilities.
- Disqualifying spam instead of archive/purge.
- Reading `crm_opportunity_lose` as the bare opportunity, or retrying the loss when `discovery.outcome` is `kept`.
- Unconfirmed workspace linking or `link_existing` without `iam.staffAssignments.create`.
- Winning without decision maker and sent/accepted proposal version.
