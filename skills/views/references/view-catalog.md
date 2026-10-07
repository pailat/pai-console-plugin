# Catálogo de vistas `pai-view@1`

> Generado por `tools/gen-references.ts` desde pai-portal `4ae9b884` (2026-10-07 Merge pull request #159 from pailat/fix/0.2.5/package-cycle), `packages/views/src/catalog.ts`. No editar a mano: regenerar.

Formato: Spec plano de json-render: { root: id, elements: { [id]: { type, props, children? } } }. Los hijos se referencian por id.

## Reglas

- Usa sólo los componentes de este catálogo; no hay className, style, colores ni HTML.
- Los ids son únicos, empiezan con letra y se reutilizan al editar.
- Las props omitidas que aceptan null toman su valor por defecto.
- Sólo AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell, Card, Collapsible, Grid, Section, Stack, Tabs, UnderlinedTabs, Tooltip y ButtonGroup tienen hijos; Tabs y UnderlinedTabs llevan un hijo por pestaña, en orden.
- Elige el layout con la raíz de la vista: AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell son pantallas completas (ver layouts) y van sólo en la raíz; un documento, reporte o tablero empieza con Stack. Nunca recrees una pantalla de Pai con AppShell: AppShell es para apps de clientes.
- Datos estáticos: escribe valores ya formateados, con su fecha de corte en el detalle o la descripción.
- Enlaces sólo a rutas del Portal (/…) o a https.
- Máximo 300 elementos y 12 niveles de anidamiento.

## Límites

- elements: 300
- characters: 200000
- depth: 12
- text: 2000
- label: 160
- items: 60
- tableColumns: 10
- tableRows: 200
- chartCategories: 60
- chartSeries: 6
- gridColumns: 6
- navItems: 12
- erdTables: 120
- erdRelations: 400
- c4Elements: 150
- c4Relations: 400
- graphNodes: 500
- graphEdges: 1500

## Layouts: la raíz de la vista

Una pantalla completa empieza con uno de estos componentes como `root` (y solo ahí). Un documento, reporte o tablero empieza con `Stack`.

- **AppShell**: Simula una aplicación completa: barra lateral con marca, menú con iconos y usuario, y un encabezado con el título de la pantalla; sus hijos son el contenido. Úsalo como raíz de la vista. En Recursos se muestra en un marco con escritorio/tableta/móvil y se abre a pantalla completa; en pantallas angostas el menú pasa a un botón.
- **AuthFrame**: Pantalla de identidad de Pai (iniciar sesión, registro, invitación), idéntica a la real: fondo animado de Pai, logo blanco y una tarjeta centrada con title y description; sus hijos van dentro de la tarjeta (Input, Button, Text, Separator…). Va siempre como raíz de la vista. Nada se envía.
- **ConsoleShell**: Pantalla de Console (el back office de Pai), idéntica a la real: selector «Consola», el menú real según lo que la persona puede hacer (admin, workforce o all), usuario al pie, la barra con migas y el título de la página con una acción opcional. Sus hijos son el contenido. Va siempre como raíz de la vista. active es la clave del ítem activo (admin.users, admin.organizations, workforce.payments…). Nada navega.
- **PortalShell**: Pantalla del Portal de Pai, idéntica a la real: selector de organización, el menú real del área (home, organization, project o product) tal como lo ve un cliente o el staff de Pai (audience), usuario al pie y la barra con migas y, para staff, «Preguntar al agente». Sus hijos son el contenido de la página. Va siempre como raíz de la vista. active es la clave del ítem activo del menú (projects, milestones, payments…). menu reemplaza el menú real sólo para pantallas que Portal aún no tiene. Nada navega.
- **SiteShell**: Página del sitio público de Pai (pai.lat), idéntica a la real: header flotante con logo, menús Soluciones/Productos/Empresa, idiomas ES/EN/PT y «Hablemos de tu proyecto»; footer con columnas y banner de cookies. Sus hijos son las secciones (SiteHero, LogoGrid, SectionIntro, ServiceCards, CtaBand…). Va siempre como raíz. page marca la página del menú (home deja el header transparente sobre el hero; contact quita el botón). Nunca uses AppShell ni PortalShell para el sitio. Nada navega.
- **Stack**: Documento, reporte o tablero dentro de una página de Recursos (sin chrome de app).

## Grupos

| Grupo | Para | Componentes |
|---|---|---|
| Aplicación | Pantallas completas: la raíz de la vista y su layout. PortalShell y ConsoleShell (las apps de Pai, con su chrome real), SiteShell (el sitio público pai.lat), AuthFrame (login y registro) y AppShell (la app de un cliente). | AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell |
| Sitio web | Secciones del sitio público de Pai (pai.lat) para usar dentro de SiteShell: hero, logos de clientes, titular con texto, tarjetas de servicios y llamada a la acción. | CtaBand, LogoGrid, SectionIntro, ServiceCards, SiteHero |
| Estructura | Contenedores que ordenan la vista: pilas, cuadrículas, tarjetas, secciones y pestañas. | Accordion, Card, Collapsible, Grid, Section, Separator, Stack, Tabs, UnderlinedTabs |
| Contenido | Títulos, texto, etiquetas, avisos, listas y enlaces. | Alert, Avatar, Badge, Heading, Item, Kbd, Link, List, StatusBadge, StatusDot, Text, Tooltip |
| Datos | Indicadores, tablas, gráficas y pares etiqueta–valor. | BarList, Chart, KeyValue, Metric, Progress, Table |
| Controles | Botones, menús y campos de formulario. Responden dentro de la vista (abren, cambian, se marcan) pero nada se envía, guarda ni navega, salvo un botón con href. | ActionMenu, Button, ButtonGroup, Calendar, Checkbox, Command, Dropzone, FilterBar, Input, RadioGroup, Select, Switch, Textarea, ToggleGroup |
| Navegación | Migas, paginación y las piezas sueltas del chrome de Pai: barra de página, selectores de organización y proyecto, cabecera de proyecto. | Breadcrumb, OrgSwitcher, PageBar, Pagination, ProjectHeader, ProjectSwitcher |
| Estados | Vacío, error y carga de una sección, con el aspecto que usan Portal y Console. | EmptyState, ErrorState, LoadingState, Skeleton, Spinner |
| Planeación | Cronologías, etapas e hitos. | Checklist, MilestoneGanttLegend, MilestoneGanttSkeleton, Stages, Timeline |
| Conocimiento | Diagramas del grafo de Conocimiento: ERD, C4 y el grafo de nodos. Se mueven y acercan dentro de la vista; los enlaces llevan a la página de cada nodo cuando la vista trae href. | C4Diagram, ErdDiagram, KnowledgeGraph |

## Componentes

Las props que aceptan `null` son opcionales en la práctica: si se omiten toman su valor por defecto. Las demás son obligatorias.

### AppShell (admite hijos)

Simula una aplicación completa: barra lateral con marca, menú con iconos y usuario, y un encabezado con el título de la pantalla; sus hijos son el contenido. Úsalo como raíz de la vista. En Recursos se muestra en un marco con escritorio/tableta/móvil y se abre a pantalla completa; en pantallas angostas el menú pasa a un botón.

- `brand`: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) }
- `nav`: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in", active?: boolean (null = por defecto) }] (min 1, máx 12)
- `secondaryTitle`: string (≤80) (null = por defecto)
- `secondaryNav`: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in", active?: boolean (null = por defecto) }] (máx 12) (null = por defecto)
- `title`: string (min 1, ≤160)
- `user`: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) } (null = por defecto)

### AuthFrame (admite hijos)

Pantalla de identidad de Pai (iniciar sesión, registro, invitación), idéntica a la real: fondo animado de Pai, logo blanco y una tarjeta centrada con title y description; sus hijos van dentro de la tarjeta (Input, Button, Text, Separator…). Va siempre como raíz de la vista. Nada se envía.

- `title`: string (min 1, ≤160) (null = por defecto)
- `description`: string (≤2000) (null = por defecto)

### ConsoleShell (admite hijos)

Pantalla de Console (el back office de Pai), idéntica a la real: selector «Consola», el menú real según lo que la persona puede hacer (admin, workforce o all), usuario al pie, la barra con migas y el título de la página con una acción opcional. Sus hijos son el contenido. Va siempre como raíz de la vista. active es la clave del ítem activo (admin.users, admin.organizations, workforce.payments…). Nada navega.

- `area`: "admin"|"workforce"|"all" (null = por defecto)
- `active`: string (≤80) (null = por defecto)
- `menu`: [{ label?: string (min 1, ≤160) (null = por defecto), items: [{ key: string (min 1, ≤80), label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" }] (min 1, máx 12) }] (min 1, máx 6) (null = por defecto)
- `breadcrumb`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 6) (null = por defecto)
- `title`: string (min 1, ≤160) (null = por defecto)
- `action`: string (min 1, ≤160) (null = por defecto)
- `user`: { name: string (min 1, ≤160), email: string (min 1, ≤160) }

### PortalShell (admite hijos)

Pantalla del Portal de Pai, idéntica a la real: selector de organización, el menú real del área (home, organization, project o product) tal como lo ve un cliente o el staff de Pai (audience), usuario al pie y la barra con migas y, para staff, «Preguntar al agente». Sus hijos son el contenido de la página. Va siempre como raíz de la vista. active es la clave del ítem activo del menú (projects, milestones, payments…). menu reemplaza el menú real sólo para pantallas que Portal aún no tiene. Nada navega.

- `area`: "home"|"organization"|"project"|"product" (null = por defecto)
- `audience`: "client"|"staff" (null = por defecto)
- `active`: string (≤80) (null = por defecto)
- `menu`: [{ label?: string (min 1, ≤160) (null = por defecto), items: [{ key: string (min 1, ≤80), label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" }] (min 1, máx 12) }] (min 1, máx 6) (null = por defecto)
- `organization`: string (min 1, ≤160) (null = por defecto)
- `organizations`: [string (min 1, ≤160)] (máx 20) (null = por defecto)
- `project`: string (min 1, ≤160) (null = por defecto)
- `projects`: [string (min 1, ≤160)] (máx 20) (null = por defecto)
- `breadcrumb`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 6) (null = por defecto)
- `user`: { name: string (min 1, ≤160), email: string (min 1, ≤160) }

### SiteShell (admite hijos)

Página del sitio público de Pai (pai.lat), idéntica a la real: header flotante con logo, menús Soluciones/Productos/Empresa, idiomas ES/EN/PT y «Hablemos de tu proyecto»; footer con columnas y banner de cookies. Sus hijos son las secciones (SiteHero, LogoGrid, SectionIntro, ServiceCards, CtaBand…). Va siempre como raíz. page marca la página del menú (home deja el header transparente sobre el hero; contact quita el botón). Nunca uses AppShell ni PortalShell para el sitio. Nada navega.

- `lang`: "es"|"en"|"pt" (null = por defecto)
- `page`: "home"|"services"|"industries"|"portal"|"about"|"manifesto"|"contact" (null = por defecto)
- `cookies`: boolean (null = por defecto)

### CtaBand

Cierre de una página del sitio: titular grande, una línea de texto y dos llamadas (primary sólida en el color de marca, secondary con flecha). centered la centra.

- `headline`: string (min 1, ≤200)
- `description`: string (≤2000) (null = por defecto)
- `primary`: string (min 1, ≤160)
- `secondary`: string (min 1, ≤160) (null = por defecto)
- `centered`: boolean (null = por defecto)

### LogoGrid

Rejilla de logos de clientes de la home de pai.lat («Equipos que confían en Pai»): celdas con línea fina, 2, 4 u 8 por fila según el ancho. Cada logo se escribe como su nombre en tipografía de marca (la vista no carga imágenes).

- `kicker`: string (min 1, ≤160) (null = por defecto)
- `logos`: [string (min 1, ≤40)] (min 2, máx 16)

### SectionIntro

Sección del sitio con titular grande a la izquierda y texto a la derecha (en móvil, uno bajo el otro), como las de la home de pai.lat. kicker es una etiqueta pequeña sobre el titular.

- `kicker`: string (min 1, ≤160) (null = por defecto)
- `title`: string (min 1, ≤200)
- `body`: string (≤2000)

### ServiceCards

Tarjetas de servicios o capacidades del sitio (2 a 6), en 1, 2 o 3 columnas: icono, título, texto y una lista corta de lo que incluye.

- `items`: [{ title: string (min 1, ≤160), body: string (≤2000), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto), points?: [string (min 1, ≤160)] (máx 6) (null = por defecto) }] (min 2, máx 6)

### SiteHero

Hero de la home de pai.lat, el real: fondo de puntos y malla de color animada a la derecha, sello opcional (badge, p. ej. «Stripe Premier Partner»), titular grande cuyo final (highlight) va en el degradado de marca, introducción y dos llamadas (primary sólida, secondary discreta). Primer hijo de SiteShell.

- `badge`: string (min 1, ≤160) (null = por defecto)
- `title`: string (min 1, ≤200)
- `highlight`: string (≤120) (null = por defecto)
- `intro`: string (≤2000)
- `primary`: string (min 1, ≤160) (null = por defecto)
- `secondary`: string (min 1, ≤160) (null = por defecto)

### Accordion

Secciones desplegables de texto (preguntas frecuentes, detalles secundarios).

- `items`: [{ title: string (min 1, ≤160), content: string (≤2000) }] (min 1, máx 60)
- `type`: "single"|"multiple" (null = por defecto)

### Card (admite hijos)

Tarjeta con título y descripción opcionales que agrupa contenido relacionado. En su encabezado puede llevar una acción (botón; con href navega) y un menú «⋯» decorativo. No la uses como encabezado de la vista ni anides tarjetas dentro de tarjetas.

- `title`: string (null = por defecto)
- `description`: string (null = por defecto)
- `maxWidth`: "sm"|"md"|"lg"|"full" (null = por defecto)
- `centered`: boolean (null = por defecto)
- `action`: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto), href?: string (null = por defecto) } (null = por defecto)
- `menu`: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto), destructive?: boolean (null = por defecto), separatorBefore?: boolean (null = por defecto) }] (min 1, máx 20) (null = por defecto)

### Collapsible (admite hijos)

Una sección desplegable con título; sus hijos se muestran al abrirla.

- `title`: string
- `defaultOpen`: boolean (null = por defecto)

### Grid (admite hijos)

Cuadrícula de 1 a 6 columnas que se apila en pantallas angostas. Úsala para tarjetas de métricas (5 o 6 en una fila de KPIs) o grupos paralelos.

- `columns`: integer (≥1, ≤6) (null = por defecto)
- `gap`: "sm"|"md"|"lg"|"xl" (null = por defecto)

### Section (admite hijos)

Región con título (h2) y descripción opcional que agrupa los bloques de un tema de la vista.

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)

### Separator

Línea divisoria entre bloques.

- `orientation`: "horizontal"|"vertical" (null = por defecto)

### Stack (admite hijos)

Contenedor flex vertical u horizontal; la base de cualquier vista. Sus hijos se apilan con el espacio indicado.

- `direction`: "horizontal"|"vertical" (null = por defecto)
- `gap`: "none"|"sm"|"md"|"lg"|"xl" (null = por defecto)
- `align`: "start"|"center"|"end"|"stretch" (null = por defecto)
- `justify`: "start"|"center"|"end"|"between"|"around" (null = por defecto)

### Tabs (admite hijos)

Pestañas. Declara las pestañas en tabs y pon un hijo por pestaña, en el mismo orden (normalmente un Stack).

- `tabs`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 8)
- `defaultValue`: string (null = por defecto)

### UnderlinedTabs (admite hijos)

Pestañas subrayadas, las de las secciones de un proyecto en Portal (Resumen, Cronograma, Pagos). Mismas props que Tabs: un hijo por pestaña, en orden.

- `tabs`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 8)
- `defaultValue`: string (null = por defecto)

### Alert

Aviso destacado: info, success, warning o error. Úsalo para conclusiones, riesgos o advertencias.

- `title`: string
- `message`: string (null = por defecto)
- `type`: "info"|"success"|"warning"|"error" (null = por defecto)

### Avatar

Iniciales de una persona (sin imagen externa).

- `name`: string
- `size`: "sm"|"md"|"lg" (null = por defecto)

### Badge

Etiqueta corta de estado o categoría.

- `text`: string
- `variant`: "default"|"secondary"|"destructive"|"outline" (null = por defecto)

### Heading

Título de una parte de la vista. h1 sólo para el título principal; luego h2 y h3.

- `text`: string
- `level`: "h1"|"h2"|"h3"|"h4" (null = por defecto)

### Item

Fila de una lista (archivo, persona, integración): icono, título, descripción y un dato a la derecha. Con href toda la fila es un enlace. Apila varios en un Stack con gap sm.

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `icon`: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto)
- `meta`: string (min 1, ≤160) (null = por defecto)
- `href`: string (null = por defecto)
- `variant`: "default"|"outline"|"muted" (null = por defecto)

### Kbd

Atajo de teclado («⌘ K», «Ctrl Enter»): una tecla por elemento de keys.

- `keys`: [string (min 1, ≤12)] (min 1, máx 4)

### Link

Enlace a una ruta del Portal (/organization/projects/…) o a un sitio https.

- `label`: string (min 1, ≤160)
- `href`: string

### List

Lista de viñetas o numerada de texto plano.

- `items`: [string (min 1, ≤640)] (min 1, máx 60)
- `ordered`: boolean (null = por defecto)

### StatusBadge

Estado con el tono de Pai (neutral, info, progress, success, warning, danger), como en las tablas de proyectos, pagos y propuestas. El texto dice el estado; el tono sólo lo refuerza.

- `label`: string (min 1, ≤160)
- `tone`: "neutral"|"info"|"progress"|"success"|"warning"|"danger"

### StatusDot

Punto de color con su texto: el estado discreto de una fila o un hito (neutral, info, progress, success, warning, danger).

- `label`: string (min 1, ≤160)
- `tone`: "neutral"|"info"|"progress"|"success"|"warning"|"danger"

### Text

Párrafo de texto plano (sin Markdown). Variantes: body, lead (introducción), muted, caption, code. tone lo colorea para una nota breve: success, warning, danger o info.

- `text`: string
- `variant`: "body"|"caption"|"muted"|"lead"|"code" (null = por defecto)
- `tone`: "success"|"warning"|"danger"|"info" (null = por defecto)

### Tooltip (admite hijos)

Muestra un texto breve al pasar el cursor o enfocar su único hijo, que no debe ser interactivo (Text, Badge, StatusBadge, Kbd): la ayuda de un dato.

- `text`: string (min 1, ≤160)

### BarList

Lista de barras horizontales con su porcentaje (ventas por vendedor, avance por área). Cada barra se mide contra max, o contra la mayor si no hay max; display reemplaza el número mostrado («$1.2 M»).

- `items`: [{ label: string (min 1, ≤160), value: number (≥0), display?: string (≤40) (null = por defecto) }] (min 1, máx 60)
- `max`: number (null = por defecto)
- `showPercent`: boolean (null = por defecto)

### Chart

Gráfica con los colores del tema: bar, line, area o pie. categories es el eje X (o las porciones de pie) y cada serie trae un valor por categoría. pie usa una sola serie. Con kind bar, orientation horizontal dibuja barras acostadas (rankings, etiquetas largas).

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `kind`: "bar"|"line"|"area"|"pie"
- `categories`: [string (min 1, ≤80)] (min 1, máx 60)
- `series`: [{ name: string (min 1, ≤80), values: [number] }] (min 1, máx 6)
- `unit`: string (≤20) (null = por defecto)
- `stacked`: boolean (null = por defecto)
- `orientation`: "vertical"|"horizontal" (null = por defecto)

### KeyValue

Pares etiqueta–valor (fechas, responsables, montos) en 1 a 3 columnas.

- `items`: [{ label: string (min 1, ≤160), value: string (min 1, ≤400) }] (min 1, máx 60)
- `columns`: integer (≥1, ≤3) (null = por defecto)

### Metric

Indicador (KPI): etiqueta, valor ya formateado («68 %», «$1.2 M»), unidad pequeña opcional («MXN») y detalle con su comparación o fecha de corte. tone colorea el valor: positive, warning, negative o info.

- `label`: string (min 1, ≤160)
- `value`: string (min 1, ≤40)
- `detail`: string (≤160) (null = por defecto)
- `trend`: "up"|"down"|"flat" (null = por defecto)
- `unit`: string (min 1, ≤12) (null = por defecto)
- `tone`: "neutral"|"positive"|"warning"|"negative"|"info" (null = por defecto)

### Progress

Barra de avance de 0 a 100 con etiqueta opcional.

- `value`: number
- `max`: number (null = por defecto)
- `label`: string (null = por defecto)

### Table

Tabla de datos: columns son los encabezados y rows un arreglo de filas con una celda por columna.

- `columns`: [string (min 1, ≤160)] (min 1, máx 10)
- `rows`: [[string (≤640)]] (máx 200)
- `caption`: string (≤160) (null = por defecto)

### ActionMenu

Menú de acciones que se abre al pulsar: sin label es el botón «⋯» de las filas y tarjetas; con label es un botón con flecha. Sus opciones son decorativas (no ejecutan nada).

- `label`: string (min 1, ≤160) (null = por defecto)
- `items`: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto), destructive?: boolean (null = por defecto), separatorBefore?: boolean (null = por defecto) }] (min 1, máx 20)
- `align`: "start"|"end" (null = por defecto)

### Button

Botón con las variantes de Pai. Con href navega (ruta del Portal o https); sin href es decorativo: se ve y se pulsa, pero no hace nada. iconOnly deja sólo el icono (label queda como nombre accesible).

- `label`: string (min 1, ≤160)
- `variant`: "default"|"secondary"|"outline"|"ghost"|"destructive"|"link" (null = por defecto)
- `size`: "sm"|"default"|"lg" (null = por defecto)
- `icon`: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto)
- `iconOnly`: boolean (null = por defecto)
- `href`: string (null = por defecto)
- `disabled`: boolean (null = por defecto)

### ButtonGroup (admite hijos)

Agrupa botones relacionados (Button, ActionMenu) pegados entre sí, como «Exportar | ⋯».

- `orientation`: "horizontal"|"vertical" (null = por defecto)

### Calendar

Calendario de un mes con fechas marcadas (entregas, reuniones). selected son fechas AAAA-MM-DD; con mode range son el inicio y el fin. Se puede cambiar de mes y elegir dentro de la vista; nada se guarda.

- `month`: string (null = por defecto)
- `selected`: [string] (máx 31) (null = por defecto)
- `mode`: "single"|"multiple"|"range" (null = por defecto)

### Checkbox

Casilla con su etiqueta (aceptar términos, marcar una opción). Se marca y desmarca dentro de la vista; nada se guarda.

- `label`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `checked`: boolean (null = por defecto)
- `disabled`: boolean (null = por defecto)

### Command

Buscador de comandos (paleta tipo ⌘K) con grupos de opciones y atajos. Filtra al escribir dentro de la vista; las opciones no ejecutan nada.

- `placeholder`: string (min 1, ≤160) (null = por defecto)
- `groups`: [{ heading?: string (min 1, ≤160) (null = por defecto), items: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto), shortcut?: string (≤20) (null = por defecto) }] (min 1, máx 20) }] (min 1, máx 6)
- `empty`: string (min 1, ≤160) (null = por defecto)

### Dropzone

Zona para arrastrar o elegir archivos (decorativa: no sube nada). accept dice qué se admite («PDF o XML, hasta 10 MB»).

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `accept`: string (≤120) (null = por defecto)
- `button`: string (min 1, ≤160) (null = por defecto)

### FilterBar

Barra de filtros sobre una tabla o tablero: buscador opcional, filtros «Etiqueta: valor» (listas que cambian dentro de la vista, sin filtrar nada) y un botón principal a la derecha.

- `search`: string (min 1, ≤160) (null = por defecto)
- `filters`: [{ label: string (min 1, ≤40), value: string (min 1, ≤80), options?: [string (min 1, ≤80)] (máx 20) (null = por defecto) }] (máx 6)
- `action`: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto), href?: string (null = por defecto) } (null = por defecto)

### Input

Campo de texto de una línea con etiqueta y ayuda opcionales. Se puede escribir en él, pero nada se envía ni se guarda.

- `label`: string (min 1, ≤160) (null = por defecto)
- `description`: string (≤2000) (null = por defecto)
- `disabled`: boolean (null = por defecto)
- `placeholder`: string (min 1, ≤160) (null = por defecto)
- `value`: string (≤400) (null = por defecto)
- `type`: "text"|"email"|"number"|"search"|"tel"|"url" (null = por defecto)

### RadioGroup

Opciones excluyentes visibles a la vez (2 a 6), con etiqueta. Cambia dentro de la vista; nada se guarda.

- `label`: string (min 1, ≤160) (null = por defecto)
- `description`: string (≤2000) (null = por defecto)
- `disabled`: boolean (null = por defecto)
- `options`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 6)
- `value`: string (null = por defecto)

### Select

Lista desplegable para elegir una opción. Se abre y cambia dentro de la vista; nada se guarda. value es la opción elegida al cargar.

- `label`: string (min 1, ≤160) (null = por defecto)
- `description`: string (≤2000) (null = por defecto)
- `disabled`: boolean (null = por defecto)
- `placeholder`: string (min 1, ≤160) (null = por defecto)
- `options`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 1, máx 60)
- `value`: string (null = por defecto)

### Switch

Interruptor de encendido/apagado con su etiqueta (preferencias, avisos). Cambia dentro de la vista; nada se guarda.

- `label`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `checked`: boolean (null = por defecto)
- `disabled`: boolean (null = por defecto)

### Textarea

Campo de texto de varias líneas (comentarios, notas). Se puede escribir, pero nada se envía.

- `label`: string (min 1, ≤160) (null = por defecto)
- `description`: string (≤2000) (null = por defecto)
- `disabled`: boolean (null = por defecto)
- `placeholder`: string (min 1, ≤160) (null = por defecto)
- `value`: string (≤2000) (null = por defecto)
- `rows`: integer (≥2, ≤12) (null = por defecto)

### ToggleGroup

Botones segmentados para cambiar de modo (Lista | Tablero, Semana | Mes). Cambia dentro de la vista; no cambia el contenido ni navega.

- `options`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto) }] (min 2, máx 6)
- `value`: string (null = por defecto)
- `variant`: "default"|"outline" (null = por defecto)

### Breadcrumb

Migas de pan: dónde está la pantalla («Proyectos › Portenta › Cronograma»). El último elemento es la página actual; los anteriores pueden llevar href.

- `items`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 8)

### OrgSwitcher

El selector de organización de Portal, solo: muestra la organización (o Pai sin organization) y se abre con «Buscar…», Pai, Consola (staff) y «Tus organizaciones». Filtra al escribir; elegir no cambia nada.

- `organization`: string (min 1, ≤160) (null = por defecto)
- `organizations`: [string (min 1, ≤160)] (máx 20) (null = por defecto)
- `staff`: boolean (null = por defecto)

### PageBar

La barra superior de una página de Portal o Console, sola: botón del menú lateral, migas, acciones a la derecha (botones decorativos) y, si assistant, «Preguntar al agente». Úsala para mostrar la barra fuera de un PortalShell/ConsoleShell (que ya la traen).

- `breadcrumb`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 6)
- `actions`: [string (min 1, ≤160)] (máx 3) (null = por defecto)
- `assistant`: boolean (null = por defecto)

### Pagination

Paginación bajo una tabla o lista: página actual de un total. Se puede cambiar de página dentro de la vista, pero el contenido no cambia.

- `page`: integer (≥1, ≤9007199254740991)
- `pages`: integer (≥1, ≤999)

### ProjectHeader

Cabecera de un proyecto de Portal (Inicio, Cronograma, Pagos…): nombre, estado (draft, planned, active, on_hold, completed, cancelled), arquitecto de Pai, fechas ya formateadas («28 jul – 18 ago») y la salud declarada (on_track, at_risk, off_track). compact es la versión de la barra del Cronograma.

- `name`: string (min 1, ≤160)
- `status`: "draft"|"planned"|"active"|"on_hold"|"completed"|"cancelled"
- `architect`: string (min 1, ≤160) (null = por defecto)
- `dates`: string (≤60) (null = por defecto)
- `health`: "on_track"|"at_risk"|"off_track" (null = por defecto)
- `compact`: boolean (null = por defecto)

### ProjectSwitcher

El selector de proyecto de las migas de Portal: el nombre del proyecto con ⌃⌄ que abre la lista buscable de projects. Elegir no navega.

- `project`: string (min 1, ≤160)
- `projects`: [string (min 1, ≤160)] (máx 30) (null = por defecto)

### EmptyState

Estado vacío de una sección, como en Portal: icono, «Aún no hay {objetos}», una línea para quien mira y una acción opcional (botón con href o decorativo).

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `icon`: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto)
- `action`: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in" (null = por defecto), href?: string (null = por defecto) } (null = por defecto)

### ErrorState

Error al cargar una sección, como en Portal: «No se pudo cargar {X}.», una explicación opcional y el botón «Reintentar» (decorativo).

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `retry`: boolean (null = por defecto)

### LoadingState

Sección cargando, como en Portal: anuncia «Cargando {sección}» a los lectores de pantalla y muestra un esqueleto con la forma del contenido (text, list, card o table).

- `label`: string (min 1, ≤160)
- `shape`: "text"|"list"|"card"|"table" (null = por defecto)
- `rows`: integer (≥1, ≤12) (null = por defecto)

### Skeleton

Bloques grises con la forma del contenido que aún no llega: text (líneas), list (filas con avatar), card (tarjeta) o table (filas de tabla).

- `shape`: "text"|"list"|"card"|"table" (null = por defecto)
- `rows`: integer (≥1, ≤12) (null = por defecto)

### Spinner

Indicador de actividad en curso (enviando, procesando) con un texto opcional al lado.

- `label`: string (min 1, ≤160) (null = por defecto)

### Checklist

Lista de verificación (documentos de un expediente, requisitos): cada punto done (Validado), pending (Pendiente) o warning (Con observaciones), con un detalle opcional. label cambia la etiqueta del estado si hace falta («Recibido»).

- `items`: [{ label: string (min 1, ≤160), status: "done"|"pending"|"warning", detail?: string (≤160) (null = por defecto), statusLabel?: string (min 1, ≤40) (null = por defecto) }] (min 1, máx 40)

### MilestoneGanttLegend

Leyenda del Cronograma de Portal: colores de estado de los hitos (pendiente, en curso, completado, vencido) y, si se indican, barras, puntos, tareas, dependencias y línea base.

- `ranges`: boolean (null = por defecto)
- `points`: boolean (null = por defecto)
- `tasks`: boolean (null = por defecto)
- `dependencies`: boolean (null = por defecto)
- `baseline`: boolean (null = por defecto)

### MilestoneGanttSkeleton

Cronograma de Portal cargando: barra de navegación, árbol de hitos y barras del Gantt en gris. Para mostrar cómo se ve la pantalla mientras llegan los datos.


### Stages

Etapas de un proceso en una línea horizontal (Prospecto › Propuesta › Negociación › Cierre): cada una done, current o upcoming, con un detalle breve opcional (fecha, responsable).

- `items`: [{ label: string (min 1, ≤160), status: "done"|"current"|"upcoming", detail?: string (≤80) (null = por defecto) }] (min 2, máx 8)

### Timeline

Cronología de hitos o eventos con fecha, título, descripción y estado (done, current, upcoming).

- `items`: [{ date: string (min 1, ≤40), title: string (min 1, ≤160), description?: string (≤2000) (null = por defecto), status?: "done"|"current"|"upcoming" (null = por defecto) }] (min 1, máx 60)

### C4Diagram

Diagrama C4 de Conocimiento, el mismo de Portal, en uno de sus cuatro niveles (context, container, component, code): elementos dentro del límite, personas y sistemas externos, relaciones con qué hacen y su tecnología (agrupadas y enrutadas para no encimarse). view es exactamente la proyección `c4` que devuelve la tool knowledge_view (no la escribas a mano). Con href, cada elemento y los botones de nivel llevan a la página del nodo ({id}, más ?level=); sin href no hay enlaces.

- `view`: object
- `href`: string (≤500) (null = por defecto)
- `height`: "sm"|"md"|"lg" (null = por defecto)

### ErdDiagram

Diagrama entidad-relación de Conocimiento, el mismo de Portal: tablas con sus columnas (PK/FK/UQ), relaciones con cardinalidad pata de gallo y, en un ERD de sistema, un marco por modelo. view es exactamente la proyección `erd` que devuelve la tool knowledge_view (no la escribas a mano). href lleva a la página de cada tabla o modelo ({id}); sin href no hay enlaces. focus resalta una tabla.

- `view`: object
- `href`: string (≤500) (null = por defecto)
- `focus`: string (≤200) (null = por defecto)
- `height`: "sm"|"md"|"lg" (null = por defecto)

### KnowledgeGraph

Grafo de Conocimiento, el mismo de Portal (WebGL): un punto por nodo, coloreado por su kind, y una línea por relación. Se arrastra, se acerca y al elegir un punto se resaltan sus vecinos y su título. Con href, el nodo elegido enlaza a su página ({id}). Usa los nodos y relaciones que devolvieron knowledge_list, knowledge_get o knowledge_context.

- `nodes`: [{ id: string (min 1, ≤200), title: string (min 1, ≤200), kind: "objective"|"decision"|"adr"|"business_rule"|"constraint"|"risk"|"question"|"assumption"|"task"|"pattern"|"runbook"|"gotcha"|"antipattern"|"note"|"concept"|"fact"|"reference"|"module"|"screen"|"flow"|"data_model"|"entity"|"component"|"actor"|"glossary_term" }] (min 1, máx 500)
- `edges`: [{ source: string (min 1, ≤200), target: string (min 1, ≤200), rel: string (min 1, ≤40) }] (máx 1500)
- `href`: string (≤500) (null = por defecto)
- `height`: "sm"|"md"|"lg" (null = por defecto)

## Ejemplo del catálogo

```json
{
 "root": "vista",
 "elements": {
  "vista": {
   "type": "Stack",
   "props": {
    "direction": "vertical",
    "gap": "lg"
   },
   "children": [
    "titulo",
    "kpis",
    "avance"
   ]
  },
  "titulo": {
   "type": "Heading",
   "props": {
    "text": "Estado del proyecto",
    "level": "h1"
   }
  },
  "kpis": {
   "type": "Grid",
   "props": {
    "columns": 3,
    "gap": "md"
   },
   "children": [
    "k1",
    "k2",
    "k3"
   ]
  },
  "k1": {
   "type": "Metric",
   "props": {
    "label": "Avance",
    "value": "68 %",
    "trend": "up"
   }
  },
  "k2": {
   "type": "Metric",
   "props": {
    "label": "Hitos cerrados",
    "value": "5 de 8"
   }
  },
  "k3": {
   "type": "Metric",
   "props": {
    "label": "Presupuesto usado",
    "value": "54 %"
   }
  },
  "avance": {
   "type": "Section",
   "props": {
    "title": "Horas por mes"
   },
   "children": [
    "grafica"
   ]
  },
  "grafica": {
   "type": "Chart",
   "props": {
    "title": "Horas por mes",
    "kind": "bar",
    "categories": [
     "Jul",
     "Ago",
     "Sep"
    ],
    "series": [
     {
      "name": "Horas",
      "values": [
       120,
       140,
       98
      ]
     }
    ],
    "unit": "h"
   }
  }
 }
}
```
