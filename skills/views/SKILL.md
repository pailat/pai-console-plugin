---
name: views
description: "UI generativa de Pai (catálogo pai-view@1, 140 componentes del sistema de diseño de Pai sobre ReUI: pantallas reales de Portal, Console y pai.lat, patrones de pantalla con regiones (tablero, detalle, lista, chat, formulario, wizard…), formularios, chat, comercio, las piezas de datos del Portal —Pagos, Cronograma, Tareas, Proyectos, Actividad, Biblioteca— y diagramas de Conocimiento). Dibuja vistas en la conversación con view_render (dashboards, comparativos, resúmenes visuales de datos ya obtenidos) o guárdalas en Recursos como bloque view de una page canvas (tableros, mockups de pantallas con AppShell, reportes visuales). Úsalo cuando pidan ver, mostrar, graficar o comparar datos de Pai de forma visual, un tablero, dashboard, mockup, wireframe o pantalla (de una app de cliente, del Portal, de Console o del sitio), dibujar un ERD, un C4 o el grafo, o editar una vista existente."
argument-hint: "[proyecto] [qué vista: tablero, pantalla, comparativo…]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# UI generativa de Pai (`pai-view@1`)

Lee antes el skill `pai-console`: entorno, descubrimiento, buscar antes de crear, CAS.

**Catálogo completo**, generado desde el código: `${CLAUDE_PLUGIN_ROOT}/skills/views/references/view-catalog.md`. Tiene los layouts de raíz, los 15 grupos, los 140 componentes con sus props, límites y un ejemplo de cada uno, y las 4 recetas del servidor completas.

`view_catalog` es la fuente del servidor:
- sin argumentos devuelve el **índice** (reglas, layouts y los componentes con sus props por nombre);
- con `{types: [...]}` o `{group}` devuelve el **esquema completo y un ejemplo** de esos componentes;
- con `{recipe}` (`dashboard`, `list-filters`, `record-detail`, `list-reading`) devuelve una **pantalla completa** lista para cambiarle los datos.

Si un componente no está en la referencia o dudas de una prop, **pide su detalle** con `view_catalog {types}` antes de usarlo. Si lo vas a hacer para muchos componentes, delégalo a `pai-explorer`.

## Tres formas en que aparece una vista

| Forma | Cuándo | Cómo |
|---|---|---|
| **Automática** | Solo las lecturas con vista propia (`project_summary`, `timeline_get`, `payment_list`, `task_board`, `knowledge_library`, `knowledge_view`…; lista en el skill `pai-console` §6). Detalles, búsquedas, validaciones y catálogos no traen vista | Solo en los hosts con MCP Apps, el resultado crudo de esa tool se dibuja solo. No sustituye un resumen: **si la persona pide ver, mostrar, graficar o comparar, compón la vista y dibújala con `view_render`**, aunque ya hayas leído los datos |
| **En la conversación** | «Muéstrame», «compara», «resume visualmente», un dashboard para responder ahora | **`view_render {title, spec}`**: dibuja la vista que compones, la valida y no guarda nada. Es una lectura: no pide confirmación ni en producción |
| **Guardada en Recursos** | Un tablero, mockup o reporte visual que el equipo o el cliente van a volver a abrir | Bloque `view` en una page `layout: "canvas"` (§ Guardar). Previsualízala antes con `view_render` |

Si dudas entre dibujar y guardar, dibuja y ofrece guardarla.

## Reglas de datos (las tres formas)

- **Solo datos que obtuviste de las tools**, en esta conversación o en la fuente que citas. Una vista no consulta nada ni inventa cifras. La excepción son los mockups, cuyos datos de ejemplo deben ser verosímiles y se marca que son mockup.
- **Valores ya formateados** en español de México: `"1 240"`, `"$412,300"` con `unit: "MXN"`, `"68 %"`, `"3.4 s"`. `Metric.value` admite como máximo 40 caracteres y `unit` como máximo 12.
- **Fecha de corte y origen siempre**, en la `description` de la `Section`, en el `detail` de una `Metric` o en el `caption` de una `Table`. Por ejemplo: «Datos de payment_list al 2026-10-06».
- Una vista no cita fuentes formales. Si cada cifra debe ir citada, usa una page de documento con `facts` o `data-table` (skill `resources`).

## El spec

```json
{ "root": "root",
  "elements": {
    "root": { "type": "Section", "props": { "title": "…", "description": "Corte al 2026-10-06" }, "children": ["kpis"] },
    "kpis": { "type": "Grid", "props": { "columns": 3, "gap": "md" }, "children": ["kpiA"] },
    "kpiA": { "type": "Metric", "props": { "label": "Cobrado", "value": "$240,000", "unit": "MXN" } }
  } }
```

- **Plano:** cada elemento se declara una vez en `elements` y se referencia por id en `children`. Tiene un solo padre, todo cuelga de `root` y no hay ciclos ni elementos sueltos.
- **Ids** en inglés y camelCase, que digan qué son (`kpiCollected`, `loansTable`). Al editar, **conserva los ids** de lo que no cambia.
- **La raíz elige el layout:**
  - una pantalla completa empieza con un shell, que va **solo en la raíz** (tabla de abajo);
  - un documento, reporte, tablero o resumen empieza con **`Stack`**.
- **Tienen hijos** solo los shells (AppShell, PortalShell, ConsoleShell, SiteShell, AuthFrame), los patrones (`*Layout`, `SplitView`), Stack, Grid, Section, Card, Frame, DialogFrame, DetailSheet, Collapsible, Tabs, UnderlinedTabs, Tooltip, Popover, ButtonGroup, Stepper, ContactSection y ProposalSummary. La lista exacta está en las reglas de la referencia.
  - Tabs y UnderlinedTabs llevan un hijo por pestaña, en orden; normalmente cada hijo es un Stack.
  - Tooltip lleva un solo hijo, no interactivo.
- **Props estrictas:** cada objeto de props es cerrado y solo lleva las del catálogo. Nada de `className`, `style`, colores, HTML ni expresiones. Las props que admiten `null` se pueden omitir.
- **Iconos:** solo los del catálogo, por ejemplo `home`, `users`, `calendar`, `wallet`, `receipt`, `reports`, `book-open`, `plus`, `download`, `check`. La lista completa está en la referencia.
- Límites: ≤300 elementos y ≤12 niveles; `KnowledgeGraph` ≤1500 aristas; `Grid` de 1 a 6 columnas; `Table` ≤10 columnas y ≤200 filas; `Chart` ≤6 series y ≤60 categorías.

## Layouts: la raíz

| Raíz | Es | Úsala para |
|---|---|---|
| `Stack` | Contenido sin pantalla alrededor | Tableros, reportes, resúmenes, comparativos y todo `view_render` de datos |
| `PortalShell` | **El Portal de Pai, idéntico al real.** `area` (home, organization, project, product), `audience` (client o staff), `active` (ítem del menú), `organization`, `project`, `breadcrumb`, `user` | Mockups de pantallas nuevas o cambios del Portal. `menu` reemplaza el menú real solo para secciones que el Portal aún no tiene |
| `ConsoleShell` | **Console, idéntico al real.** `area` (admin, workforce o all), `active` (`admin.users`, `workforce.payments`…), `breadcrumb`, `title`, `action`, `user` | Mockups del back office |
| `SiteShell` | **pai.lat, idéntico al real.** `lang`, `page`, con hijos del grupo Sitio web: `SiteHero`, `LogoGrid`, `SectionIntro`, `ServiceCards`, `HowItWorks`, `Testimonials`, `BlogList`, `CtaBand`, `ContactSection` | Páginas o secciones del sitio |
| `AuthFrame` | **Login, registro e invitación de Pai** | Pantallas de identidad, con `Input` y `Button` dentro |
| `AppShell` | **La app de un cliente**, con su marca y su menú | Mockups de los productos que Pai construye para un cliente |

**Nunca recrees una pantalla de Pai con `AppShell`:** para el Portal usa `PortalShell` y para Console `ConsoleShell`. Ya traen el menú, las migas y el usuario reales, así que no los dibujes a mano. Para piezas sueltas del chrome fuera de un shell están `PageBar`, `OrgSwitcher`, `ProjectSwitcher` y `ProjectHeader`.

## Piezas de pantalla de Pai: con los datos de su tool

Estos componentes son las pantallas reales del Portal y de Console. Se alimentan con la respuesta de una tool: **dásela casi tal cual, sin inventar filas.** El ejemplo de cada uno en la referencia muestra la forma exacta.

| Componente | Datos de | Es |
|---|---|---|
| `ProjectsTable` | `project_list` | «Proyectos» de una organización |
| `OrganizationsGrid` / `OrganizationMembers` | `organization_list` / `organization_get` | Inicio del Portal / miembros e invitaciones |
| `ActivityFeed` | `project_activity` | Actividad por día (`variant`: recent en Portal, log en Console) |
| `MilestoneTimeline` | `timeline_get` | El Cronograma real: hitos, tareas, dependencias y línea base |
| `TaskBoard` | `task_board` | El tablero de Tareas real (cuatro columnas fijas) |
| `Payments` | `payment_list` | «Pagos»: facturas abiertas, siguiente cobro y pagado; montos en unidades, nunca datos bancarios |
| `ProposalSummary` / `ProposalLifecycle` | `proposal_get` | Resumen comercial / ciclo enviada, aceptada o rechazada |
| `ProductsList` / `ProductDetail` | `product_list` / `product_get` | Productos y el Inicio de un producto |
| `Resources` | `page_list` / `file_list` | Una carpeta de Recursos |
| `KnowledgeTable` | `knowledge_library` / `knowledge_search` | La biblioteca de Conocimiento |
| `CommentsPanel` / `HistoryPanel` | `comment_list` / `page_versions` | Los paneles del riel de un documento |

Genéricos que imitan esas pantallas con datos propios:
- `DataTable`: columnas tipadas, búsqueda, filtros, orden y páginas;
- `Kanban`: un tablero sin dominio; para tareas de Pai usa `TaskBoard`;
- `DetailSheet`: el panel lateral de detalle;
- `KnowledgeKindBadge`: el tipo de un nodo.

En el sitio, `ContactSection` es el «Hablemos» de pai.lat, dentro de `SiteShell`.

Todos funcionan **dentro de la vista** (filtran, ordenan, arrastran, abren) y **nada se guarda ni navega**.

Úsalos para combinar varias piezas en una vista (por ejemplo `ProjectHeader` + `MilestoneTimeline` + `Payments`), para mockups de pantallas nuevas dentro de `PortalShell` o `ConsoleShell`, o para guardar un tablero en Recursos.

## Qué componente usar

| Necesito… | Usa | No uses |
|---|---|---|
| Un KPI | `Metric`, con `unit` y `tone` (`positive`, `warning`, `negative`, `info`) | Texto suelto con la cifra |
| El estado de algo | **`StatusBadge`** con su tono (neutral, info, progress, success, warning, danger), como en el Portal; `StatusDot` en filas | `Badge` para estados: `Badge` es para categorías |
| Partes de un total o un ranking | `BarList` (con `display` para el valor formateado) | `Chart` `pie` con muchas porciones |
| Evolución en el tiempo | `Chart` `line`, `area` o `bar` | `Table` |
| Detalle tabular | `Table` (simple, con `caption` del corte o del top N) o `DataTable` (tipada, con búsqueda, filtros y páginas) | |
| Datos clave de una ficha | `KeyValue` (1–3 columnas) | |
| Un proceso por etapas | **`Stages`** (done, current, upcoming) | `Timeline`, que es para fechas y eventos |
| Requisitos o entregables con estado | **`Checklist`** | `List` |
| Hitos con fecha | `Timeline`; el Cronograma completo, `MilestoneTimeline` | |
| Una lista de archivos, personas o integraciones | `Item` apilados en un `Stack` `gap: "sm"` | `List` |
| Secciones de un proyecto como en el Portal | `UnderlinedTabs` | `Tabs` |
| Una conclusión o un riesgo | `Alert` (uno; el que hay que atender) | Varios `Alert` |
| La cabecera de un proyecto (estado, arquitecto, fechas, salud) | `ProjectHeader` | KeyValue + Badge armados a mano |
| Un ERD | **`ErdDiagram`**, con `view` = la proyección `erd` de `knowledge_view {format:"json"}` **tal cual** | Tablas o Mermaid a mano |
| Un C4 | **`C4Diagram`**, con `view` = la proyección `c4` de `knowledge_view` tal cual | Cajas con Card |
| El grafo de Conocimiento | **`KnowledgeGraph`**, con `nodes` y `edges` de `knowledge_graph` (o de `knowledge_get` / `knowledge_context`), ≤1500 aristas | |

**Controles y estados son de mockup:**
- Button, ButtonGroup, ActionMenu, FilterBar, ToggleGroup, Input, Select, Textarea, Checkbox, RadioGroup, Switch, Calendar, Command, Dropzone, Pagination, Breadcrumb, OrgSwitcher y ProjectSwitcher **no envían, guardan ni navegan**: responden dentro de la vista y nada más. Un `Button` o un `Link` con `href` solo navega.
- EmptyState, ErrorState, LoadingState, Skeleton, Spinner, MilestoneGanttLegend y MilestoneGanttSkeleton dibujan los estados de una pantalla.

Úsalos para **mockups de pantallas**, no en un dashboard de datos reales: ahí darían a entender que se puede filtrar o actuar.

## Diagramas de Conocimiento

Los diagramas se dibujan con los datos del servidor, **nunca escritos a mano**.

**ERD:**
1. `knowledge_view {view: "erd", scope: "data_model/<slug>", format: "json"}`.
2. `view_render` con la respuesta **tal cual** en `view`:

```json
{ "title": "ERD — Modelo de ventas",
  "spec": { "root": "root", "elements": {
    "root": { "type": "Stack", "props": { "direction": "vertical", "gap": "md" }, "children": ["erd"] },
    "erd": { "type": "ErdDiagram", "props": { "view": <respuesta de knowledge_view>, "height": "lg" } } } } }
```

- `href`: la ruta del nodo con `{id}`, para que cada tabla enlace a su página.
- `focus`: resalta una tabla.

**C4:** igual, con `view: "c4"` y su `level`, en un `C4Diagram`.

## Patrones: pantallas con regiones

Dentro de un shell (o en la raíz), un **patrón** reparte la pantalla en regiones con nombre: lleva **un hijo por región, en el orden de sus regiones**, y `regions` elige cuáles usa (en ese mismo orden). Cada región trae su marco, así que no envuelvas los hijos en `Card`.

| Patrón | Para |
|---|---|
| `DashboardLayout` | Tablero: `kpis` (Stats), `main` (Chart o DataTable), `side` (BarList, Timeline, Item), `footer` (DataTable) |
| `PageLayout` | Sección de producto: `header` (PageHeader, ProjectHeader), `toolbar` (FilterBar, botones), `main` (DataTable, Kanban…), `aside` |
| `DetailLayout` | Detalle de un registro: `header`, `summary` (KeyValue, Stats), `main` (Tabs, Section…), `aside` |
| `SplitView` | Lista y lectura: `list` y `detail` |
| `BoardLayout` | Tablero o agenda: `toolbar`, `board` (Kanban, Gantt, TaskBoard, EventCalendar), `aside` |
| `FilesLayout` | Explorador: `tree` (Tree), `list` (FileList, DataTable), `preview` |
| `DocLayout` | Documento largo: `header`, `toc`, `content` |
| `FormLayout` | Formulario de maqueta: `intro`, `fields`, `actions` |
| `WizardLayout` | Alta guiada: `steps` (Stages), `main`, `actions` |
| `SettingsLayout` | Ajustes: `nav` y `main` |
| `ChatLayout` | Chat de maqueta con un agente: `thread` (ChatThread), `composer` (ChatComposer), `aside` |
| `AuthLayout` | Acceso o registro de **la app de un cliente** (para Pai usa `AuthFrame`): `brand`, `form`, `aside` |
| `EmptyLayout` | Estado vacío rico: `visual`, `message`, `actions`, `preview` |

Antes de usar un patrón pide su esquema con `view_catalog {types}`: las regiones y qué va en cada una están en su descripción.

**Grafo:** `knowledge_graph {projectId}`. Convierte sus nodos a `{id, title, kind}` y sus aristas a `{source, target, rel}`, y pásalos a `KnowledgeGraph` (≤1500 aristas).

Úsalos para mostrar en la conversación lo que modelaste (skills `erd` y `c4`) o, guardados, en un reporte de arquitectura en Recursos.

## Recetas

**Del servidor** (`view_catalog {recipe}`; también completas al final de la referencia): `dashboard` (AppShell + DashboardLayout), `list-filters` (encabezado, filtros y tabla), `record-detail` (detalle con pestañas y lateral) y `list-reading` (SplitView). Para la pantalla de una app de cliente, **parte de la receta más cercana** y cambia sus datos.

**Del plugin**: cada una tiene un ejemplo completo y validado en `${CLAUDE_PLUGIN_ROOT}/skills/views/examples/`. Parte de él.

1. **Resumen en la conversación** (`render-payments-summary.json`, `view_render`): `Stack` → `Section` con origen y corte → `Grid` de `Metric` → `BarList` → `Item` con lo siguiente.
2. **Tablero de KPIs** (`kpi-dashboard.json`): `Section` con `StatusBadge` de salud y un `Alert` → `Grid` de 4 `Metric` → `UnderlinedTabs` con `Stages` + `Table` y `Chart` + `BarList`.
3. **Pantalla del Portal** (`portal-screen.json`): `PortalShell` (`area: "project"`, `audience`, organización, proyecto, migas y usuario) → `Stack` con `ProjectHeader` y una `Card` con `FilterBar` e `Item`. Para Console es igual, con `ConsoleShell`.
4. **Mockup de app de cliente** (`app-screen.json`): `AppShell` (brand, `nav` con uno `active`, `title`, `user`) → `Breadcrumb` → KPIs → `Alert` → `Card` con `action` y `menu`, que contiene `FilterBar` + `Table` + `Pagination`.
   - Se ve en un marco de escritorio, tableta o móvil y se abre a pantalla completa.
   - Para los estados vacíos o de error de la pantalla, haz variantes con `EmptyState` o `ErrorState`.
   - Liga el mockup desde el nodo `screen` (skill `screens`) con `wireframe: {description, pageId}`.
5. **Reporte visual o ficha** (`visual-report.json`): `Heading` h1 + `Text` lead → `Stages` → `KeyValue` → `Progress` → `Checklist` de entregables → `Timeline` → `Accordion`.
6. **Comparativo** (`comparison.json`): `Stack` → `Section` → `Grid` de `Card`, una por opción, con `StatusBadge` (Recomendada, Alternativa o Descartada), `KeyValue` y `List` → `Alert` `info` con la conclusión. No anides `Card` dentro de `Card`.

## Diseño

- **Jerarquía:** un título (`Section` o `Heading` h1) y debajo bloques del mismo nivel. `Grid` para lo paralelo, `Stack` para lo secuencial, pestañas para vistas alternativas del mismo dato.
- **Menos es más:** cada elemento responde una pregunta. No pongas gráfica y tabla con los mismos números en la misma pestaña. Usa 3 o 4 métricas por fila.
- **`tone` y `trend` con intención:** `trend` solo con comparación real (di contra qué en `detail`), y `tone: "negative"` o `"warning"` solo para lo que exige atención.
- Etiquetas cortas y en español. Sin ids ni jerga técnica en vistas para el cliente.

## Guardar en Recursos

1. Busca (`page_search`, `page_list`) si ya existe la vista; si existe, edítala.
2. Compón el spec y **previsualízalo con `view_render`**. Si da errores, corrige lo que dice.
3. `page_validate` con la page: `layout: "canvas"`, un bloque `{id, type: "view", title, spec}` y **sin `typeSlug`**, porque ningún tipo built-in admite `view`.
4. `page_create`:
   - `path` en inglés por carpeta: `dashboards/…`, `mockups/…`, `reports/…`;
   - `audience`: `internal` o `client`;
   - `summary` ≤80 e `idempotencyKey` estable.

**Editar:**
1. `page_read {view: "full"}`.
2. Cambia el spec sobre esa copia, conservando los ids.
3. `view_render` para revisar, luego `page_validate`.
4. `page_update` con `expectedDocumentId` y `expectedRevision`.

## Errores frecuentes (de `view_render` y `page_validate`)

| Mensaje | Causa |
|---|---|
| `Componente desconocido «X». Consulta el catálogo de vistas.` | Un `type` fuera de `pai-view@1` |
| `Unrecognized key: "className"` | Prop fuera del catálogo |
| `El hijo «x» no existe.` | Un id de `children` que no está en `elements` |
| `«x» ya es hijo de «y»; cada elemento tiene un solo padre.` | El mismo id en dos `children` |
| `«x» no está conectado a la raíz; enlázalo como hijo o elimínalo.` | Un elemento suelto |
| `Tabs declara N pestaña(s) y tiene M hijo(s): pon uno por pestaña.` | `tabs` y `children` de distinto largo (también en UnderlinedTabs) |
| `La serie «S» tiene N valor(es) y hay M categoría(s).` | Una serie de `Chart` sin un valor por categoría |
| `bloque-no-permitido` | La page lleva `typeSlug`: quítalo |

**Nunca inventes componentes, props ni iconos.** Si algo no está en el catálogo, compónlo con lo que hay o dilo. Si el servidor (`view_catalog`) ofrece algo que la referencia no tiene, manda el servidor.
