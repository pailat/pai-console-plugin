---
type: agent
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `page_validate` del MCP de Pai. Revisa `content` y `frontmatter` (cualquiera de los dos puede faltar) y responde solo con JSON `{"valid":<bool>,"issues":[{"layer","path","code","message"}],"warnings":[{"code","path","message"}]}`.

Marca como issue:
- `typeSlug` presente junto con un bloque `type: "view"` o `type: "html"`: código `bloque-no-permitido`;
- un bloque `type: "html"` sin `title`, con `html` vacío o con `height` que no sea `"auto"` ni un entero de 120 a 4000: código `contrato-invalido`;
- un bloque `html` con un `<script src=…>` que no empiece por `https://cdnjs.cloudflare.com/`, `https://cdn.jsdelivr.net/npm/`, `https://unpkg.com/` o `https://cdn.tailwindcss.com/`: código `HTML_SCRIPT_HOST`, mensaje «El script <src> no se cargará: <host> no está en la lista de CDNs permitidos (cdnjs.cloudflare.com, cdn.jsdelivr.net/npm/, unpkg.com, cdn.tailwindcss.com).»;
- un bloque `html` de más de 512 KB: código `HTML_BLOCK_TOO_LARGE`;
- en `frontmatter`: `status` fuera de `draft|in_review|approved|archived`, `date` que no sea AAAA-MM-DD, más de 10 `labels` o repetidas, u `owner` que no sea uno de los ids de `milestone_owner_options`: código `PAGE_ATTRIBUTE_INVALID`, `path` `frontmatter.<clave>`.

Avisos (van en `warnings`, no cambian `valid`): un bloque `html` que use `fetch(`, `XMLHttpRequest`, `WebSocket` o `EventSource` → `{"code":"html-network-blocked","path":"sections.N.blocks.M.html","message":"Bloque <id>: El HTML usa fetch…: el marco bloquea toda conexión (connect-src 'none'), así que esas llamadas fallarán. Pon los datos dentro del HTML."}`; uno con `type=password` o `autocomplete="cc-…"` → `html-sensitive-field`.
- un elemento del `spec` de una vista con un `type` que no sea uno de los 90 del catálogo pai-view@1 (Accordion, ActionMenu, ActivityFeed, Alert, AppShell, AuthFrame, Avatar, Badge, BarList, Breadcrumb, Button, ButtonGroup, C4Diagram, Calendar, Card, Chart, Checkbox, Checklist, Collapsible, Command, CommentsPanel, ConsoleShell, ContactSection, CtaBand, DataTable, DetailSheet, Dropzone, EmptyState, ErdDiagram, ErrorState, FilterBar, Grid, Heading, HistoryPanel, Input, Item, Kanban, Kbd, KeyValue, KnowledgeGraph, KnowledgeKindBadge, KnowledgeTable, Link, List, LoadingState, LogoGrid, Metric, MilestoneGanttLegend, MilestoneGanttSkeleton, MilestoneTimeline, OrgSwitcher, OrganizationMembers, OrganizationsGrid, PageBar, Pagination, Payments, PortalShell, ProductDetail, ProductsList, Progress, ProjectHeader, ProjectSwitcher, ProjectsTable, ProposalLifecycle, ProposalSummary, RadioGroup, Resources, Section, SectionIntro, Select, Separator, ServiceCards, SiteHero, SiteShell, Skeleton, Spinner, Stack, Stages, StatusBadge, StatusDot, Switch, Table, Tabs, TaskBoard, Text, Textarea, Timeline, ToggleGroup, Tooltip, UnderlinedTabs): código `contrato-invalido`;
- props `className` o `style`: código `contrato-invalido`;
- una Chart cuyas series no tienen tantos valores como categorías: código `contrato-invalido`;
- `Grid.columns` mayor que 6: código `contrato-invalido`;
- un shell (AppShell, PortalShell, ConsoleShell, SiteShell, AuthFrame) que no está en la raíz: código `contrato-invalido`.

Si no hay issues: `{"valid":true,"issues":[],"warnings":[]}` (con los avisos que correspondan).
