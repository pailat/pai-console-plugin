# Pai corp MCP tool inventory (0.2.5+)

**Source:** pai-portal `feat/0.2.5/reui` @ 04278b49d, including CRM-1..4, ATE-204 HTML blocks, CRM #178 and ATE-224..227 whiteboards (`apps/api/src/modules/mcp/tools/*.ts`).

Tools declare annotations, read by the guard from server-generated `hooks/tools.json`. All project tools take `organizationId` and `projectId`. `knowledge_*`, `task_board` and `knowledge_view` also accept `productId` for product knowledge linked to the project. Content writes to a closed project return `CONFLICT`.

**Leyenda:**
- **L**: read. Allowed without confirmation in any environment.
- **E**: write. Requires confirmation in production.
- **IRR**: irreversible. Production confirmation explains its consequences.

## Identidad y descubrimiento

| Tool | Tipo | Note |
|---|---|---|
| `whoami` | L | Staff o cliente, scopes |
| `organization_list` | L | `query`, `limit` ≤100 |
| `organization_get` | L | Miembros, invitaciones y proyectos |
| `organization_create` | E | Caller becomes admin; ownerEmail sends an invitation |
| `organization_slug_set` | E | Staff. Change the organization slug in Portal URLs; the old slug redirects and cannot be reused |
| `organization_update` | E | Requires organization owner/admin, like other organization settings. Update display name or logo (fileKey from organization_logo_upload_url; empty string removes it); slug stays unchanged |
| `organization_logo_upload_url` | E | Signed organization-logo PUT URL: PNG only, ≤10 MB. Used for the selector avatar and Settings > General, distinct from the SVG-capable theme logo; upload both |
| `organization_member_role_set` | E | owner, admin or member (memberId from organization_get); never leaves the organization without an owner |
| `organization_member_remove` | E | Remove a member and free a seat; cannot remove the last owner |
| `organization_invitation_cancel` | E | Invalidate the emailed invitation link |
| `me_profile_update` | E | Update your display name or image (fileKey from me_avatar_upload_url) |
| `me_avatar_upload_url` | E | Signed avatar PUT URL (PNG ≤10 MB) |
| `project_list` | L | |
| `project_summary` | L | |
| `project_status` | L | |
| `project_activity` | L | |
| `project_create` | E | Initial status is draft; dates are ISO |
| `project_update` | E | |
| `project_slug_set` | E | Staff. Change project slug in Portal URLs; the old slug redirects |
| `project_invite_client` | E | Email a client invitation |
| `project_delete` | E · IRR | **Cascade-deletes payments and CFDI records** |
| `project_close_review` | L | Outstanding tasks, questions, risks and suggestions before closure, with their resolution actions; informational, not blocking |
| `project_close` | E | Make project read-only (completed or cancelled); each product records knowledge_merged |
| `project_reopen` | E | Reopen a closed project; audited |
| `status_update_list` | L | |
| `status_update_publish` | E | Immediately visible to the client |
| `brief_list` | L | |
| `brief_get` | L | |
| `brief_agenda` | L | |
| `brief_update_status` | E | new → reviewing → converted |

## Organization theme

See skill `theme` for workflow, errors, tokens and Portal verification. The organization brand controls Portal and client views: colors, font, radius, shadow, logos and Portal app `shell` (ATE-212). This matches Settings > Appearance (`organization:appearance`, staff only). Workflow: `organization_theme_get` → `organization_theme_preview` → `organization_theme_save_draft` → `organization_theme_publish`.

Supply the complete `theme`: `{schemaVersion: 1, light, dark, font, radius, shadow, shell, logo: {light, dark}}`. `shell` is `sidebar`, `floating`, `header`, `dual-rail`, `section-tabs`, `framed`, `topbar`, `icon-rail`, or null for Pai; other values produce a shell issue. View `PortalShell` uses the published theme.

| Tool | Tipo | Note |
|---|---|---|
| `organization_theme_get` | L | Published theme, draft with AA/schema/logo issues, and versions; read before editing |
| `organization_theme_preview` | L | Validate a theme or draft without saving: AA contrast issues, CSS, available shells (null id means Pai), and preview |
| `organization_theme_save_draft` | E | Create a new draft without changing the published theme; AA issues are allowed in drafts |
| `organization_theme_publish` | E | Visible on next client load; rejects invalid AA contrast, schema or logos |
| `organization_theme_revert` | E | Copy a version to a draft and publish unless publish is false |
| `organization_theme_logo_upload_url` | E | Five-minute signed logo PUT URL: PNG, WebP or SVG ≤512 KB with declared contentType and size |
| `organization_theme_logo_confirm` | E | After PUT (storageKey equals fileKey), validate and return {storageKey, contentType, bytes}. Supply this complete object in theme.logo.light/dark; a string is rejected |

## Resources

| Tool | Tipo | Note |
|---|---|---|
| `folder_create` | E | Create an empty Resources folder (parent empty string means Resources root); returns path for note_create |
| `folder_delete` | E · IRR | Only empty folders at any depth, including internal pages/files; removes empty descendants. summary required (≤80, audited). Root cannot be deleted (invalid_input); nonempty is CONFLICT; inaccessible or not yours is FORBIDDEN |
| `note_create` | E | Markdown note; staff notes default to internal unless audience is client |
| `note_update` | E | Update body/attributes with expectedRevision. A Pai agent can only propose suggestions on client notes ({suggested: true}) |
| `note_audience_set` | E | client publishes to the client organization; internal limits visibility to the Pai team |
| `whiteboard_create` | E | Resources whiteboard (Excalidraw), empty or content {graph}/{mermaid}; never coordinates. Staff boards default internal unless audience is client. See resources §3 |
| `whiteboard_read` | L | Semantic nodes, connections, groups, otherCount, revision and WhiteboardSketch preview |
| `whiteboard_update` | E | expectedRevision and idempotencyKey required; append adds on the right, linking existing nodes by id/text; replace erases human drawings and requires an explicit request. Open boards update live |
| `page_frontmatter_update` | E | Merge-patch audience and frontmatter attributes (date, owner, status, labels) with expectedRevision |
| `page_projection` | L | Render a page projection block (C4, ERD, screen, flow) like the Portal reader |
| `page_suggest` | E | Propose reviewable Before/After changes instead of applying them; baseRevision from page_read |
| `page_suggestion_decide` | E | Accept/reject suggestions in a set; accepted changes apply together |
| `quiz_respond` | E | Answer a quiz on behalf of the user; every attempt counts |
| `page_catalog` | L | About 35 KB: blocks, rules, JSON Schema and views. Prefer local resources/views references |
| `page_types` | L | List types, or fetch one slug with its authoringGuide |
| `page_validate` | L | Validate content/frontmatter without saving; returns issues and warnings (HTML warnings and WHITEBOARD_NOT_FOUND, WHITEBOARD_NOT_A_BOARD, WHITEBOARD_NOT_CLIENT_VISIBLE) |
| `page_list` | L | Filters status, owner, labels, dateFrom/dateTo, audience, pathPrefix; sort path/date/status. Follow nextCursor with the same sort. Includes attributes |
| `page_search` | L | limit ≤50, no cursor/order; page_list filters apply after selecting 50 results, so fewer than limit may return |
| `page_read` | L | view summary/content/full; use full before writing. Includes typed attributes, resolved projections and whiteboards (title/summary or hidden) |
| `page_versions` | L | Paginate with nextCursor |
| `page_version` | L | |
| `page_comprehension` | L | Read before rewriting a page |
| `page_create` | E | summary ≤80; idempotencyKey required; no images; derivedFromPageId links the source note; warnings returned |
| `page_update` | E | Full replacement with CAS |
| `page_restore` | E | Restore a version as a new revision |
| `page_move` | E | Rewrite links; inspect warnings |
| `page_migrate` | E | Convierte Markdown legacy a Pages |
| `page_asset_upload` | E | Signed image PUT URL for an existing page (png/jpeg/webp/gif ≤10 MB). Remains pending until page_create/page_update references and checks it. Does not use asset_confirm |
| `asset_list` | L | Visible project image/video assets: kind (image/video/other), q, cursor; includes href and usedIn. Search before upload. Returns a view |
| `asset_get` | L | Asset dimensions/duration, uploader, usedIn and canDelete |
| `asset_upload` | E | Prepare upload: PNG/JPEG/WebP/GIF ≤10 MB, SVG ≤1 MB, MP4/WebM ≤200 MB; exact size; documentId targets the edited page/note/whiteboard, omitted for staff-only gallery. Returns signedUrl (PUT, 300s), headers and href; not idempotent |
| `asset_confirm` | E | After PUT, sniff bytes against declared type and sanitize SVG; marks ready. Failure returns invalid_input with reason and deletes the file |
| `asset_delete` | E · IRR | Only unused assets (otherwise CONFLICT ASSET_IN_USE), by staff or uploader |
| `page_comment_reply` | E | |
| `page_delete` | E · IRR | Hard delete, no trash |
| `file_list` | L | |
| `file_get` | L | |
| `file_download_url` | L | |
| `file_upload` | E | Signed upload URL (≤100 MiB, expires after five minutes) |
| `file_create` | E | Register an uploaded file |
| `file_update` | E | |
| `file_delete` | E · IRR | |

## Knowledge

| Tool | Tipo | Note |
|---|---|---|
| `knowledge_query` | L | Query by property, label, containment scope, related neighbors or typed pattern path (≤4 steps); limit ≤200 |
| `knowledge_batch` | E | Up to 200 atomic create/update/link/unlink/supersede/archive/resolve operations with $name refs and idempotencyKey; set-status requires a person and returns HUMAN_CONFIRMS to agents |
| `knowledge_kinds` | L | Kinds, templates and ontology catalog. Local reference: skills/knowledge/references/ |
| `knowledge_search` | L | Topic search, limit ≤25, no cursor |
| `knowledge_library` | L | **Organization inventory/table:** projectId plus kinds, paginate limit/offset to total; hybrid search with query |
| `knowledge_graph` | L | Organization or project nodes, edges and hubs |
| `knowledge_get` | L | `ref`: uuid, slug, `kind/slug` o `kb:` |
| `knowledge_context` | L | |
| `knowledge_impact` | L | |
| `knowledge_audit` | L | |
| `knowledge_view` | L | Graph-derived ERD (view erd) or C4 (view c4, level), data, Mermaid and Portal URL |
| `task_board` | L | Task board columns plus each task revision and moves |
| `knowledge_create` | E | Agents must supply sources |
| `knowledge_update` | E | expectedRevision required; supplied properties replace the complete object |
| `knowledge_link` | E | |
| `knowledge_observe` | E | Record a usage signal without changing revision |
| `knowledge_resolve` | E | Resolve a question, assumption, risk or task |
| `knowledge_supersede` | E | Replacement node must be active |
| `knowledge_revive` | E | |
| `knowledge_archive` | E | Reversible using knowledge_revive |
| `knowledge_unlink` | E · IRR | |

Clients have read-only Knowledge access (ATE-237): `knowledge_kinds`, `knowledge_search`, `knowledge_get`, `knowledge_impact` and `knowledge_view` for client-visible nodes. New kinds include `action`, `integration` and `flow_run`; only `flow_run_start` creates flow_run.

## Flows (skill `flows`)

| Tool | Tipo | Note |
|---|---|---|
| `flow_list` | L | Project flows: ref, version, steps, roles and latest run |
| `flow_get` | L | Steps with actor/screen/action/integration refs, transitions, revision, version and recent runs; renders Flow view |
| `flow_create` | E | Staff; sources required. Without graph, initialize start/end |
| `flow_save` | E | Staff. Replace the complete graph (graph or mermaid) with expectedRevision and idempotencyKey; omitted steps are deleted |
| `flow_version_bump` | E | Staff. Labeled v1-to-v2 increment without changing revision |
| `flow_run_start` | E | Start a run with actor node and mode sample or simulated; real not yet supported |
| `flow_run_step` | E | stepKey, result passed/noted/failed/skipped, branchLabel and integrationResponse; only the initiator |
| `flow_run_finish` | E | Finish as passed, passed_with_notes, failed (stoppedAtKey), or abandoned |
| `flow_run_list` | L | Flow runs, newest first |
| `flow_run_get` | L | Run details and steps |

## Cronograma

| Tool | Tipo | Note |
|---|---|---|
| `timeline_get` | L | |
| `milestone_list` | L | |
| `milestone_get` | L | |
| `milestone_owner_options` | L | |
| `milestone_create` | E | amount in cents; default currency **usd** |
| `milestone_update` | E | |
| `milestone_reorder` | E | |
| `milestone_dependency_create` | E | finish_to_start; rechaza ciclos |
| `milestone_dependency_update` | E | |
| `milestone_dependency_delete` | E | |
| `task_dependency_create` | E | Entre nodos `task`; rechaza ciclos |
| `task_dependency_update` | E | |
| `task_dependency_delete` | E | |
| `milestone_baseline_capture` | E · IRR | Once per milestone |
| `milestone_delete` | E · IRR | Its CFDI records lose their milestone |

## Propuestas y pagos

| Tool | Tipo | Note |
|---|---|---|
| `proposal_list` | L | |
| `proposal_get` | L | |
| `payment_list` | L | |
| `payment_file_download_url` | L | 60-second signed URL for receipt/invoice PDF/XML (fileId from payment_list); use immediately, never persist |
| `proposal_save` | E | Drafts only; default currency **mxn** |
| `proposal_set_status` | E · IRR | draft → sent → accepted/rejected |
| `milestone_proposal_link` | E | |
| `payment_file_upload` | E | PDF ≤10 MB; PUT within five minutes |
| `payment_cfdi_import` | E · IRR | Issuer must be the Pai RFC |
| `payment_record` | E · IRR | Record money and recalculate milestone payment status |
| `payment_void` | E · IRR | Permanently void the payment |

## Productos

| Tool | Tipo | Note |
|---|---|---|
| `product_list` | L | missing[] and hint explain missing configuration |
| `product_get` | L | |
| `product_provisioning_get` | L | |
| `product_logs` | L | |
| `product_member_list` | L | |
| `product_create` | E | |
| `product_update` | E | |
| `product_environment_set` | E | Change only the Pai database record |
| `product_environment_remove` | E | Remove only the Pai database record |
| `product_domain_set` | E | Change only the Pai database record |
| `product_domain_remove` | E | Remove only the record; does not disconnect Railway |
| `product_link_set` | E | |
| `product_link_remove` | E | |
| `product_link_project` | E | role creates, improves (default), or maintains; enables productId in project knowledge_* tools |
| `product_unlink_project` | E | |
| `product_member_add` | E | |
| `product_member_update` | E | |
| `product_request_status` | E | live requires approval by another person |
| `product_decide_status` | E | |
| `product_provision` | E · IRR | Create GitHub repository and Railway project |
| `product_deploy` | E · IRR | Production requires commitSha |
| `product_variables_set` | E · IRR | Values never returned; optional redeploy |
| `product_domain_attach` | E · IRR | Return dnsRecords |
| `product_production_access_set` | E · IRR | Redeploy production |
| `product_member_remove` | E · IRR | |

## Vistas (UI generativa)

| Tool | Tipo | Note |
|---|---|---|
| `view_catalog` | L | pai-view@1 components/props/rules/examples; supply only one of types/group, recipe or recipeGroup. Prefer the views skill reference |
| `view_render` | L | Validate/render a composed {title, spec} in the conversation without persistence; organizationId applies the organization theme |

On hosts supporting MCP Apps, reads with a built-in view render automatically: `project_summary`, `project_list`, `project_activity`, `project_close_review`, `status_update_list`, `timeline_get`, `milestone_list`, `payment_list`, `proposal_list`, `task_board`, `file_list`, `page_list`, `page_suggestions`, `page_comprehension`, `page_knowledge_health`, `page_projection`, `whiteboard_read`, `asset_list`, `flow_get`, `agent_inbox`, `knowledge_library`, `knowledge_graph`, `knowledge_view`, `organization_theme_preview`, CRM reads (`crm_overview_get`, `crm_lead_list`, `crm_lead_summary`, `crm_lead_get`, `crm_lead_record`, `crm_lead_event_list`, `crm_lead_duplicates`, `crm_lead_organization_suggestions`, `crm_submission_get`, `crm_opportunity_list`, `crm_opportunity_summary`, `crm_opportunity_get`, `crm_opportunity_event_list`, `crm_trace_get`) and `view_render`. `knowledge_view` and `page_projection` use `ui://pai/canvas.html`. Other reads (details, searches, validation and catalogs) return data and text only (ATE-203).

## CRM (staff or Console roles with `crm:access`; `crm:*` permissions)

See skill `crm`. Every lead/opportunity write carries `expectedRevision`. Amounts are cents; never sum MXN and USD.

| Tool | Tipo | Note |
|---|---|---|
| `crm_access_get` | L | Permissions crm:access/edit/convert/revenue/purge/import/join from crm.viewer, crm.sales, crm.closer, crm.admin or custom roles |
| `crm_overview_get` | L | CRM overview, funnel, attention queue, tasks and conversions. from/to (YYYY-MM-DD, ≤366 days) compare periods; ownerLoad counts open records per owner |
| `crm_owner_list` | L | Possible owners (ids for ownerUserId) |
| `crm_submission_get` | L | Forms submission and generated lead |
| `crm_submission_spam` | E | Archive submission without creating a lead |
| `crm_lead_list` | L | query, source, owner, period, waitingOn (attention, none, outsideSla...), archived filters |
| `crm_lead_summary` | L | Your attention queue, response time, SLA breaches and missing next steps |
| `crm_lead_get` | L | Lead revision, next step and chain |
| `crm_lead_record` | L | Complete qualification, submission, workspace, opportunities, seeded nodes and activity |
| `crm_lead_event_list` | L | Lead history (≤200); amounts require crm:revenue |
| `crm_lead_duplicates` | L | **Before creating:** same email, same domain and customer organizations |
| `crm_lead_organization_suggestions` | L | Similar organizations and fields that would be populated; never links |
| `crm_lead_create` | E | Referral/manual/MCP lead; firstTask required, phone optional; emails owner/team |
| `crm_lead_import` | E | crm:import. Historical lead/organization/opportunity/notes/tasks with original stages/dates; externalRef ensures idempotency (created false on replay) |
| `crm_lead_note_add` | E | Append-only lead history note ≤20,000 characters; corrections require another note. Does not move stage or next step |
| `crm_lead_create_from_submission` | E | Create lead from Forms submission |
| `crm_lead_update` | E | Datos, propietario o `stage: contacted` (exige `nextTask`) |
| `crm_lead_task_create` | E | Lead task; crm_task_create also supports opportunities/accounts |
| `crm_lead_task_complete` | E | Complete a task; nextTask required for the last task |
| `crm_lead_qualify` | E | Four qualification criteria plus workspace; seed knowledge and first Discovery opportunity |
| `crm_lead_disqualify` | E | Disqualify with a listed reason and archive |
| `crm_lead_mark_duplicate` | E | Link to surviving lead and archive duplicate |
| `crm_lead_workspace_open` | E | Create/link organization and open Discovery project; cannot relink |
| `crm_lead_workspace_join` | E | crm:join. Audited membership as admin of lead organization; unavailable without permission |
| `crm_lead_archive` | E | Remove from board without deleting |
| `crm_lead_unarchive` | E | |
| `crm_lead_purge` | E · IRR | Hard-delete unlinked junk (spam, test, mistake); crm:purge required |
| `crm_organization_list` | L | Organizations eligible for a new opportunity (≤20) |
| `crm_organization_get` | L | Account leads, Portal people, open and won opportunities |
| `crm_opportunity_list` | L | crm:revenue. Filter stage, owner, waitingOn, line, offer, kind, currency, market mx/br and close date |
| `crm_opportunity_summary` | L | Forecast per currency, win rate, your attention queue and paused opportunities |
| `crm_opportunity_get` | L | Revision, contacts, proposals/versions, activity and history |
| `crm_opportunity_event_list` | L | Recent changes across opportunities; crm:revenue |
| `crm_trace_get` | L | Submission-to-product chain with asOf |
| `crm_opportunity_create` | E | kind, line/offers, amounts in cents, market mx/br (not currency), discoveryPaid and required task |
| `crm_opportunity_update` | E | Open stage change requires nextTask; update data (including market/discoveryPaid), owner or linked proposal |
| `crm_opportunity_hold` | E | Pause; task.dueAt is the resume date |
| `crm_opportunity_lose` | E | Mark lost with listed reason |
| `crm_opportunity_probability` | E | Set probability 0–100 with reason, or reset; crm:revenue |
| `crm_opportunity_note_add` | E | Append-only opportunity note ≤20,000 characters; does not move stage |
| `crm_opportunity_contact_add` | E | Contact by leadId/userId with role |
| `crm_opportunity_contact_primary` | E | Mark primary contact |
| `crm_opportunity_contact_remove` | E | Remove contact while preserving history |
| `crm_opportunity_archive` | E | Remove from board and forecast |
| `crm_opportunity_unarchive` | E | |
| `crm_opportunity_win` | E · IRR | Win with accepted proposal version, delivery owner, start and decision_maker; crm:convert |

### CRM tasks

Task shape: `{body, dueAt, waitingOn, type?, detail?, priority?, tags?}`. `body` is the short title; `detail` is Markdown (≤20,000); type is todo|call|email|meeting; priority is low|medium|high; tags has at most ten entries. This shape applies to firstTask, task and nextTask. Use Mexico City time for dueAt: without a time, use T18:00:00-06:00 (the no-time convention); otherwise use the actual time. Never use midnight or noon UTC.

| Tool | Tipo | Note |
|---|---|---|
| `crm_task_list` | L | Console board (todo, in_progress, waiting, done). Defaults to your open tasks, most overdue first, with counts overdue/today/week/later. Filters owner (me/all/id), status, subject, due, priority, tag and query |
| `crm_task_get` | L | Task detail, type, priority, tags, status and record |
| `crm_task_tag_list` | L | Team tags by usage; inspect before creating |
| `crm_task_create` | E | Open lead, open/paused opportunity or account (record.kind account, id organizationId); future date; optional ownerUserId |
| `crm_task_update` | E | Reschedule/reassign waitingOn, type, priority, full tags, detail or progress (todo ↔ in_progress). New body archives and replaces the task with a different id |
| `crm_task_complete` | E | Complete; nextTask required if this is the last open task on an open lead/opportunity |

## Otros

| Tool | Tipo | Note |
|---|---|---|
| `comment_list` | L | Cursor pagination |
| `comment_history` | L | |
| `comment_recipients` | L | |
| `comment_create` | E | audience agent, team (staff default), client or person (audienceUserId); needsAgent; page comments require anchor |
| `comment_reply` | E | |
| `comment_edit` | E | Own comments only; marked edited |
| `comment_resolve` | E | Page threads only |
| `comment_reopen` | E | Page threads only |
| `comment_send_to_agent` | E | Page threads only; create a separate agent thread with optional body, preserving the original |
| `agent_list` | L | |
| `agent_get` | L | |
| `agent_create` | E | |
| `agent_update` | E | |
| `agent_delete` | E · IRR | To retire an agent, set status archived |
| `credit_balance` | L | |
| `credit_transactions` | L | No purchase or balance adjustment |
