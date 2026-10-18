---
name: views
description: "Compose Pai generative UI with pai-view@1: real Portal/Console/pai.lat screens, region layouts, forms/chat/commerce, data components, and Knowledge diagrams. Use view_render for conversational dashboards, comparisons, or summaries, or save canvas-page view blocks in Resources for dashboards, screen mockups, and visual reports. Applies to visual Pai data requests, dashboards, wireframes, app/Portal/Console/site screens, ERD/C4/graph rendering, or editing existing views."
argument-hint: "[project] [dashboard, screen, comparison, or other view]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Pai generative UI (`pai-view@1`)

Read shared `pai-console` first through the current client's skill mechanism: environment, discovery, search before create, CAS.

**Code-generated catalog:** `references/view-catalog.md`: root layouts, 15 groups, 152 components, props/limits/examples, 68 full server recipes. `view_catalog` is authoritative:
- No arguments: **index**, rules/layouts, component props by name.
- `{types: [...]}` / `{group}`: full schemas/examples.
- `{recipeGroup}` (`application`, `data-grid`, `chart`, `solutions`, `ecommerce`, `marketing`, `ai-agents`): recipe summaries, without views.
- `{recipe}` (`dashboard`, `list-filters`, `record-detail`, `crm-pipeline`, `site-pricing`, `shop-checkout`, `ai-chat`…): complete screen ready for new data.

When missing from references or unsure of a prop, **fetch detail** with `view_catalog {types}` before use. For large catalog reads, use Claude `pai-explorer` or the Codex generated package's explorer adapter only if available/authorized; otherwise read directly. Never assume Claude agents/tools exist in Codex.

## Three presentation modes

| Mode | When | Behavior |
|---|---|---|
| **Automatic** | Dedicated-view reads (`project_summary`, `timeline_get`, `payment_list`, `task_board`, `knowledge_library`, `knowledge_view`…; `pai-console` §6). No views for details/search/validation/catalogs | Raw tool result may render on MCP Apps hosts. For explicit show/chart/compare requests, compose `view_render` even after reading data |
| **Conversation** | Immediate visual answer/comparison/dashboard | `view_render {title, spec}` validates/renders without saving; a read requiring no write confirmation, even in production |
| **Saved Resources** | Reusable dashboard/mockup/report | `view` block in `layout: "canvas"` page; preview with `view_render` first |

When unsure, render first and offer saving; do not save without authorization. **CLI requires a text fallback** with supported figures/diagram structure, citations, and Portal links. Tool success/spec validity does not prove widget rendering; claim it only with observable client evidence. If a visual tool is absent, explain the limitation and provide text without inventing components or substituting a write.

## Data rules (all modes)

- **Only tool data** from this conversation or a cited source. Views query nothing and invent no figures. Mockups may use plausible example data, explicitly labeled mockup.
- Preserve **Mexican Spanish business formatting**: `"1 240"`, `"$412,300"` with `unit: "MXN"`, `"68 %"`, `"3.4 s"`. `Metric.value` ≤40 characters, `unit` ≤12. Replies follow user's language; keep required business locale, currencies, `America/Mexico_City` dates.
- **Always include source/as-of date** in `Section.description`, `Metric.detail`, or `Table.caption`, e.g. data from payment_list as of 2026-10-06.
- For client views send `organizationId` to `view_render` to use the published organization theme (nonmembers get Pai). Without it, uses sole organization or Pai when multiple.
- Views do not provide formal source citations; if each figure requires one, use a document page with `facts`/`data-table` (`resources`).

## Spec

```json
{ "root": "root",
  "elements": {
    "root": { "type": "Section", "props": { "title": "…", "description": "As of 2026-10-06" }, "children": ["kpis"] },
    "kpis": { "type": "Grid", "props": { "columns": 3, "gap": "md" }, "children": ["kpiA"] },
    "kpiA": { "type": "Metric", "props": { "label": "Collected", "value": "$240,000", "unit": "MXN" } }
  } }
```

- **Flat:** declare each element once in `elements`, reference IDs in `children`; one parent, connected to `root`, no cycles/orphans.
- Meaningful English camelCase IDs (`kpiCollected`, `loansTable`); **preserve unchanged IDs** while editing.
- **Root chooses layout:** full screen uses a shell **at root only**; documents/reports/dashboards/summaries use **`Stack`**.
- Only these accept children: shells (AppShell, PortalShell, ConsoleShell, SiteShell, AuthFrame), patterns (`*Layout`, `SplitView`), Stack, Grid, Section, Card, Frame, DialogFrame, DetailSheet, Collapsible, Tabs, UnderlinedTabs, Tooltip, Popover, ButtonGroup, Stepper, ContactSection, ProposalSummary. Exact list in catalog rules. Tabs/UnderlinedTabs: one ordered child per tab, usually Stack. Tooltip: one noninteractive child.
- **Named slots:** ChatComposer, Card, Item also accept `slots: {name: ["id", …]}` with the same parent/root/cycle rules. Only permitted component types per slot; unknown slot/type fails validation. Index lists slot names; detail lists types.

| Component | Slot | Types | Placement |
|---|---|---|---|
| ChatComposer | `toolbar` | Select, Button, Badge, Popover | Below text, after attachment |
| ChatComposer | `leading` | Select, Button, Badge | Before attachment |
| ChatComposer | `trailing` | Select, Button, Badge | Before send |
| Card | `header` | Badge, StatusBadge, Button, Select, Avatar | Beside title, before `action`/`menu` |
| Item | `trailing` | Badge, StatusBadge, Button, Switch | Right instead of `meta`; disables row link even with `href` |

Put controls belonging inside a component (chat scope selector, card-header badge) in its slot, not an adjacent Stack.

**Sizing/placement** (Stack/Grid only; closed values, omission preserves prior behavior):
- `width: "fit" | "full"`; full fills parent even inside `align: "center"`, where it otherwise shrinks.
- `maxWidth: "sm" | "md" | "lg" | "xl" | "full"`: readable width.
- `grow: true`: consumes remaining parent Stack space; direct shell child fills below topbar.
- `selfAlign: "start" | "center" | "end" | "stretch"`: overrides parent alignment for self.
- Stack-only `minHeight: "screen" | "half"`: vertical centering outside shells.

`justify` vertically centers when Stack has height (`grow` inside shell, `minHeight` outside). Wrap other components in Stack for placement/limits. Centering recipe:

```json
"body":   { "type": "Stack", "props": { "direction": "vertical", "grow": true }, "children": ["top", "center"] },
"center": { "type": "Stack", "props": { "direction": "vertical", "grow": true, "align": "center", "justify": "center" }, "children": ["title", "box"] },
"box":    { "type": "Stack", "props": { "width": "full", "maxWidth": "lg" }, "children": ["composer"] }
```

- **Strict props:** catalog only; no `className`, `style`, colors, HTML, expressions. Nullable props may be omitted.
- **Icons:** catalog only, e.g. `home`, `users`, `calendar`, `wallet`, `receipt`, `reports`, `book-open`, `plus`, `download`, `check`; full list in reference.
- Limits: ≤300 elements, ≤12 levels; `KnowledgeGraph` ≤1500 edges; `Flow` ≤60 nodes/120 arrows; `Grid` 1–6 columns; `Table` ≤10 columns/200 rows; `Chart` ≤6 series/60 categories (radar/radial ≤12).

## Root layouts

| Root | Contract | Use |
|---|---|---|
| `Stack` | Content without screen chrome | Dashboards/reports/summaries/comparisons, all data `view_render` |
| `PortalShell` | Actual Pai Portal: `area` home/organization/project/product, `audience` client/staff, `active`, `organization`, `project`, `breadcrumb`, `user`; published organization shell/colors (`organizationId` in `view_render`), draft in theme preview, Pai default if none; no shell-selector prop | New/changed Portal screens; `menu` override only for nonexistent Portal sections |
| `ConsoleShell` | Actual Console: `area` admin/workforce/all, `active` such as `admin.users`/`workforce.payments`, `breadcrumb`, `title`, `action`, `user` | Back-office mockups |
| `SiteShell` | Actual pai.lat: `lang`, `page`; SiteHero, LogoGrid, SectionIntro, ServiceCards, HowItWorks, Testimonials, BlogList, CtaBand, ContactSection | Site pages/sections |
| `AuthFrame` | Pai login/registration/invitations | Identity screens with Input/Button |
| `AppShell` | Client app's own brand/menu | Client product mockups |

**Never use AppShell for Pai screens.** PortalShell/ConsoleShell already provide menu/breadcrumb/user; never redraw. Separate chrome components: PageBar, OrgSwitcher, ProjectSwitcher, ProjectHeader.

## Real Pai screen components

Supply tool response **nearly unchanged, never invented rows**; exact shape in reference examples.

| Component | Tool | Content |
|---|---|---|
| `ProjectsTable` | `project_list` | Organization projects |
| `OrganizationsGrid` / `OrganizationMembers` | `organization_list` / `organization_get` | Portal home / members/invitations |
| `ActivityFeed` | `project_activity` | Daily activity; variant recent in Portal, log in Console |
| `MilestoneTimeline` | `timeline_get` | Milestones/tasks/dependencies/baseline |
| `TaskBoard` | `task_board` | Four fixed columns |
| `Payments` | `payment_list` | Open invoices/next collection/paid; amounts in units, no banking data |
| `ProposalSummary` / `ProposalLifecycle` | `proposal_get` | Commercial summary / sent-accepted-rejected lifecycle |
| `ProductsList` / `ProductDetail` | `product_list` / `product_get` | Products/product home |
| `Resources` | `page_list` / `file_list` | Resources folder |
| `KnowledgeTable` | `knowledge_library` / `knowledge_search` | Knowledge library |
| `CommentsPanel` / `HistoryPanel` | `comment_list` / `page_versions` | Document rail panels |

Generic alternatives: `DataTable` typed columns/search/filter/sort/pagination; `Kanban` for domain-free boards (Pai tasks use TaskBoard); `DetailSheet` for side detail; `KnowledgeKindBadge` for node kind. `ContactSection` is pai.lat contact section within SiteShell.

Interactions **stay inside the view** (filter/sort/drag/open), with **no persistence/navigation**. Combine pieces (ProjectHeader + MilestoneTimeline + Payments), mock new Portal/Console screens, or save dashboards.

## Component selection

| Need | Use | Avoid |
|---|---|---|
| KPI | `Metric`, `unit`, intentional `tone` (positive, warning, negative, info) | Loose numeric text |
| State | `StatusBadge` tone neutral/info/progress/success/warning/danger; row `StatusDot` | `Badge`, which is categorical |
| Ranking/parts of total | `BarList`, formatted `display` | Many-slice pie |
| Time evolution | `Chart` line/area/bar | Table |
| Tabular detail | `Table` with as-of/top-N `caption`, or typed/searchable/paginated `DataTable` | |
| Record key facts | `KeyValue`, 1–3 columns | |
| Process stages | `Stages` done/current/upcoming | Timeline, for dates/events |
| Decisions/dependency flow | `Flow`, labeled arrows, start/step/decision/end/note, ≤60 nodes | Cards/text arrows; use whiteboard_create (`resources`) for manual editing |
| Multidimensional profile/progress to goal | Chart radar/radial ≤12 categories, `max`, radial `center` | Repeated Progress |
| Saved images/screenshots/video | `Image`, `Carousel`, `Video` with visible ready project `assetId`; reuse asset_list or asset_upload/confirm (`resources` §5) | URLs; `view_render` rejects media |
| Stateful requirements/deliverables | `Checklist` | List |
| Dated milestones | Timeline; full schedule MilestoneTimeline | |
| Files/people/integrations | Item in Stack gap sm | List |
| Portal project sections | UnderlinedTabs | Tabs |
| Conclusion/risk | One actionable Alert | Many Alerts |
| Project header/status/architect/dates/health | ProjectHeader | Hand-built KeyValue/Badge |
| ERD | ErdDiagram with unmodified `knowledge_view {format:"json"}` ERD `view` | Manual tables/Mermaid |
| C4 | C4Diagram with unmodified C4 `view` | Card boxes |
| Knowledge graph | KnowledgeGraph with knowledge_graph nodes/edges (or knowledge_get/context), ≤1500 edges | |

**Mockup controls/states:** Button, ButtonGroup, ActionMenu, FilterBar, ToggleGroup, Input, Select, Textarea, Checkbox, RadioGroup, Switch, Calendar, Command, Dropzone, Pagination, Breadcrumb, OrgSwitcher, ProjectSwitcher respond locally, **never submit/save/navigate**, except Button/Link with `href` navigate only. `ChatComposer`/slots disabled unless **`interactive: true`**, which enables typing/attachment/send controls without sending/saving. Inside a mock form it remains disabled. Never substitute Textarea plus loose buttons to force typing; it distorts the screen. EmptyState, ErrorState, LoadingState, Skeleton, Spinner, MilestoneGanttLegend, MilestoneGanttSkeleton represent screen states. Use these in screen mockups, not live-data dashboards where they imply working filters/actions.

## Knowledge diagrams

Always use **server data, never hand-authored diagrams**.

ERD:
1. `knowledge_view {view: "erd", scope: "data_model/<slug>", format: "json"}`.
2. `view_render` with unchanged response as `view`:

```json
{ "title": "ERD — Sales model",
  "spec": { "root": "root", "elements": {
    "root": { "type": "Stack", "props": { "direction": "vertical", "gap": "md" }, "children": ["erd"] },
    "erd": { "type": "ErdDiagram", "props": { "view": <knowledge_view response>, "height": "lg" } } } } }
```

`href` supplies node path with `{id}` to link tables; `focus` highlights a table. C4 works the same with `view: "c4"`, its `level`, and C4Diagram.

For an already saved page `projection` ERD/C4, use **`page_projection {path, blockId}`**, with `blockId` from page_read, preserving reader visibility and client MCP support. Never rebuild through knowledge_view/view_render.

## Region patterns

Patterns inside a shell/root have **one child per chosen region in region order**; `regions` selects them in that order. Regions already frame content; do not wrap children in Card. Fetch `view_catalog {types}` before using a pattern; descriptions define regions/content.

| Pattern | Regions/content |
|---|---|
| DashboardLayout | `kpis` Stats, `main` Chart/DataTable, `side` BarList/Timeline/Item, `footer` DataTable |
| PageLayout | `header` PageHeader/ProjectHeader, `toolbar` FilterBar/buttons, `main` DataTable/Kanban…, `aside` |
| DetailLayout | `header`, `summary` KeyValue/Stats, `main` Tabs/Section…, `aside` |
| SplitView | `list`, `detail` |
| BoardLayout | `toolbar`, `board` Kanban/Gantt/TaskBoard/EventCalendar, `aside` |
| FilesLayout | `tree` Tree, `list` FileList/DataTable, `preview` |
| DocLayout | `header`, `toc`, `content` |
| FormLayout | Mock form: `intro`, `fields`, `actions` |
| WizardLayout | `steps` Stages, `main`, `actions` |
| SettingsLayout | `nav`, `main` |
| ChatLayout | `thread` ChatThread, `composer` ChatComposer with control slots, `aside`; new empty chat centers composer using grow/maxWidth lg recipe |
| AuthLayout | **Client app** login/registration: `brand`, `form`, `aside`; Pai uses AuthFrame |
| EmptyLayout | `visual`, `message`, `actions`, `preview` |

Graph: `knowledge_graph {projectId}`; adapt nodes to `{id, title, kind}`, edges to `{source, target, rel}` for KnowledgeGraph, ≤1500 edges. Show modeled ERD/C4 in conversation or saved Resources architecture report.

## Recipes

Server: 68 recipes/7 groups, `view_catalog {recipeGroup}` summaries, `{recipe}` complete; also at reference end. Examples: dashboard (AppShell + DashboardLayout), list-filters, record-detail, list-reading (SplitView), crm-pipeline, settings, wizard, flow, questionnaire, site-*, shop-*. For client app screens, **start from closest recipe and replace data**.

Useful components:
- Image/Carousel (≤12 slides), Video MP4/WebM use **project `assetId`, never URL**; required image `alt`, video `title`. Reuse visible ready assets across pages/notes/gallery. **Saved page views only**; view_render rejects them.
- Flow: horizontal/vertical processes/approvals/dependencies; start/end/step/decision/note, labeled arrows; ≤60 nodes/120 arrows.
- ShellPicker displays theme shell presets from organization_theme_preview, never saves.

Plugin validated examples in `examples/`; start from them:
1. `render-payments-summary.json`: Stack → Section source/as-of → Grid/Metric → BarList → Item next step, conversational view_render.
2. `kpi-dashboard.json`: Section/health StatusBadge/Alert → Grid of 4 Metric → UnderlinedTabs with Stages/Table and Chart/BarList.
3. `portal-screen.json`: PortalShell project area/audience/org/project/breadcrumb/user → Stack/ProjectHeader/Card/FilterBar/Item; Console equivalent uses ConsoleShell.
4. `app-screen.json`: AppShell brand/nav (one active)/title/user → Breadcrumb/KPIs/Alert/Card action/menu with FilterBar/Table/Pagination. Desktop/tablet/mobile frame/fullscreen; use EmptyState/ErrorState variants. Screen prototype page follows existing `pantallas/<product>/<screen>` convention and screen `prototype: {pageId, blockId?}` (`screens`); always `view`, never `html`.
5. `visual-report.json`: Heading h1/Text lead → Stages/KeyValue/Progress/Checklist/Timeline/Accordion.
6. `comparison.json`: Stack/Section/Grid of one Card per option with StatusBadge, KeyValue, List → info Alert conclusion. No Card inside Card.

## Design

- One Section/Heading h1 title, equal-level blocks; Grid for parallel, Stack sequential, tabs for alternate views of same data.
- Each element answers a question. No chart/table duplicating figures in one tab; 3–4 metrics/row.
- `trend` requires actual comparison explained in `detail`; negative/warning tones only for issues requiring attention.
- Short Spanish business labels where required; no IDs/technical jargon in client views. Maintained synthetic examples use English; conversation follows user's language.

## Save in Resources

Use `view` for catalog-only, no-JavaScript dashboards/reports/comparisons/Pai/client screen mockups. For custom JS/simulation/canvas/pixel-precise or unsupported interactions use isolated, network-free **`html`** with CSS theme variables (`resources` §3). `view_render` never renders HTML; saved HTML displays in Portal.

1. Search page_search/page_list; edit equivalents.
2. Compose and **preview `view_render`**; correct reported errors, disclose CLI presentation limits.
3. `page_validate`: `layout: "canvas"`, `{id, type: "view", title, spec}`, **no `typeSlug`** (no built-in type permits view).
4. `page_create`: English folder path `dashboards/…`, `mockups/…`, `reports/…`; explicit `audience` internal/client; summary ≤80; stable idempotencyKey.

Edit: full page_read → modify copy preserving IDs → view_render/page_validate → page_update with expectedDocumentId/expectedRevision.

## Common errors

Literal server messages are deliberately preserved:

| Message | Cause |
|---|---|
| `Componente desconocido «X». Consulta el catálogo de vistas.` | Type outside pai-view@1 |
| `Unrecognized key: "className"` | Unsupported prop |
| `El hijo «x» no existe.` | children ID absent from elements |
| `«x» ya es hijo de «y»; cada elemento tiene un solo padre.` | Multiple parents |
| `«x» no está conectado a la raíz; enlázalo como hijo o elimínalo.` | Orphan |
| `Tabs declara N pestaña(s) y tiene M hijo(s): pon uno por pestaña.` | Tab/child counts differ (also UnderlinedTabs) |
| `La serie «S» tiene N valor(es) y hay M categoría(s).` | Chart series/category lengths differ |
| `bloque-no-permitido` | Remove page typeSlug |
| `ASSET_ADAPTATION_REQUIRED: …` | URL instead of assetId; upload asset (`resources` §5) |
| `NOT_FOUND` for assetId | Wrong project/pending/invisible; asset_list or asset_confirm |

**Never invent components, props, or icons.** Compose from catalog or explain missing support. Server `view_catalog` takes precedence over stale references.
