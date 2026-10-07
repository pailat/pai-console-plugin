# Catálogo de vistas `pai-view@1`

> Generado por `tools/gen-references.ts` desde pai-portal `c364c4ab` (2026-10-07 Merge pull request #166 from pailat/fix/0.2.5/release-clean-2), `packages/views/src/catalog.ts`. No editar a mano: regenerar.

Formato: Spec plano de json-render: { root: id, elements: { [id]: { type, props, children? } } }. Los hijos se referencian por id.

## Reglas

- Usa sólo los componentes de este catálogo; no hay className, style, colores ni HTML.
- Cada objeto de props es cerrado: sólo las props de su esquema; las demás se rechazan.
- Los ids son únicos, empiezan con letra y se reutilizan al editar.
- Las props omitidas que aceptan null toman su valor por defecto.
- Sólo AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell, ContactSection, Card, Collapsible, DetailSheet, Grid, Section, Stack, Tabs, UnderlinedTabs, Tooltip, ButtonGroup y ProposalSummary tienen hijos; Tabs y UnderlinedTabs llevan un hijo por pestaña, en orden.
- Elige el layout con la raíz de la vista: AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell son pantallas completas (ver layouts) y van sólo en la raíz; un documento, reporte o tablero empieza con Stack. Nunca recrees una pantalla de Pai con AppShell: AppShell es para apps de clientes.
- Antes de usar un componente, pide su esquema y su ejemplo con view_catalog({ types: [...] }) o por grupo (view_catalog({ group })); aquí sólo están sus props por nombre (nombre? es opcional).
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
| Sitio web | Secciones del sitio público de Pai (pai.lat) para usar dentro de SiteShell: hero, logos de clientes, titular con texto, tarjetas de servicios, llamada a la acción y «Hablemos» (contacto en dos columnas). | ContactSection, CtaBand, LogoGrid, SectionIntro, ServiceCards, SiteHero |
| Estructura | Contenedores que ordenan la vista: pilas, cuadrículas, tarjetas, secciones, pestañas y el panel de detalle de un elemento. | Accordion, Card, Collapsible, DetailSheet, Grid, Section, Separator, Stack, Tabs, UnderlinedTabs |
| Contenido | Títulos, texto, etiquetas, avisos, listas y enlaces; los paneles de comentarios e historial de un documento. | Alert, Avatar, Badge, CommentsPanel, Heading, HistoryPanel, Item, Kbd, Link, List, StatusBadge, StatusDot, Text, Tooltip |
| Datos | Indicadores, tablas, gráficas y pares etiqueta–valor. | BarList, Chart, DataTable, KeyValue, Metric, Progress, Table |
| Controles | Botones, menús y campos de formulario. Responden dentro de la vista (abren, cambian, se marcan) pero nada se envía, guarda ni navega, salvo un botón con href. | ActionMenu, Button, ButtonGroup, Calendar, Checkbox, Command, Dropzone, FilterBar, Input, RadioGroup, Select, Switch, Textarea, ToggleGroup |
| Navegación | Migas, paginación y las piezas sueltas del chrome de Pai: barra de página, selectores de organización y proyecto, cabecera de proyecto. | Breadcrumb, OrgSwitcher, PageBar, Pagination, ProjectHeader, ProjectSwitcher |
| Estados | Vacío, error y carga de una sección, con el aspecto que usan Portal y Console. | EmptyState, ErrorState, LoadingState, Skeleton, Spinner |
| Planeación | Cronologías, etapas e hitos; el Cronograma, el tablero de Tareas y un Kanban genérico. | Checklist, Kanban, MilestoneGanttLegend, MilestoneGanttSkeleton, MilestoneTimeline, Stages, TaskBoard, Timeline |
| Proyecto | Piezas de las pantallas de un proyecto en Portal y Console: propuestas, pagos, productos. Sólo muestran lo que la vista trae; nada se guarda. | ActivityFeed, OrganizationMembers, OrganizationsGrid, Payments, ProductDetail, ProductsList, ProjectsTable, ProposalLifecycle, ProposalSummary, Resources |
| Conocimiento | Conocimiento: los diagramas del grafo (ERD, C4 y el grafo de nodos), la biblioteca de nodos y el badge de tipo de un nodo. Los diagramas se mueven y acercan dentro de la vista; los enlaces llevan a la página de cada nodo cuando la vista trae href. | C4Diagram, ErdDiagram, KnowledgeGraph, KnowledgeKindBadge, KnowledgeTable |

## Componentes

Cada objeto de props es cerrado. `?` marca una prop opcional; las que aceptan `null` toman su valor por defecto si se omiten. Las props «que vienen de» una tool se copian tal cual de su respuesta.

### Grupo: Aplicación

#### AppShell (admite hijos)

Simula una aplicación completa: barra lateral con marca, menú con iconos y usuario, y un encabezado con el título de la pantalla; sus hijos son el contenido. Úsalo como raíz de la vista. En Recursos se muestra en un marco con escritorio/tableta/móvil y se abre a pantalla completa; en pantallas angostas el menú pasa a un botón.

- `brand`: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) }
- `nav`: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap", active?: boolean (null = por defecto) }] (min 1, máx 12)
- `secondaryTitle`?: string (≤80) (null = por defecto)
- `secondaryNav`?: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap", active?: boolean (null = por defecto) }] (máx 12) (null = por defecto)
- `title`: string (min 1, ≤160)
- `user`?: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) } (null = por defecto)

Ejemplo: `{"brand":{"name":"Portenta","detail":"Ciclo de venta"},"nav":[{"label":"Dashboard","icon":"dashboard","active":true},{"label":"Ventas","icon":"file"},{"label":"Clientes","icon":"users"}],"title":"Dashboard comercial","user":{"name":"Julio César Vega","detail":"Dirección Comercial"}}`

#### AuthFrame (admite hijos)

Pantalla de identidad de Pai (iniciar sesión, registro, invitación), idéntica a la real: fondo animado de Pai, logo blanco y una tarjeta centrada con title y description; sus hijos van dentro de la tarjeta (Input, Button, Text, Separator…). Va siempre como raíz de la vista. Nada se envía.

- `title`?: string (min 1, ≤160) (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)

Ejemplo: `{"title":"Inicia sesión","description":"Entra con el correo de tu organización."}`

#### ConsoleShell (admite hijos)

Pantalla de Console (el back office de Pai), idéntica a la real: selector «Consola», el menú real según lo que la persona puede hacer (admin, workforce o all), usuario al pie, la barra con migas y el título de la página con una acción opcional. Sus hijos son el contenido. Va siempre como raíz de la vista. active es la clave del ítem activo (admin.users, admin.organizations, workforce.payments…). Nada navega.

- `area`?: "admin"|"workforce"|"all"|null (null = por defecto)
- `active`?: string (≤80) (null = por defecto)
- `menu`?: [{ label?: string (min 1, ≤160) (null = por defecto), items: [{ key: string (min 1, ≤80), label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap" }] (min 1, máx 12) }] (min 1, máx 6) (null = por defecto)
- `breadcrumb`?: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 6) (null = por defecto)
- `title`?: string (min 1, ≤160) (null = por defecto)
- `action`?: string (min 1, ≤160) (null = por defecto)
- `user`: { name: string (min 1, ≤160), email: string (min 1, ≤160) }

Ejemplo: `{"area":"admin","active":"admin.organizations","breadcrumb":[{"label":"Administración"},{"label":"Organizaciones"}],"title":"Organizaciones","action":"Agregar organización","user":{"name":"Ana López","email":"ana@pai.lat"}}`

#### PortalShell (admite hijos)

Pantalla del Portal de Pai, idéntica a la real: selector de organización, el menú real del área (home, organization, project o product) tal como lo ve un cliente o el staff de Pai (audience), usuario al pie y la barra con migas y, para staff, «Preguntar al agente». Sus hijos son el contenido de la página. Va siempre como raíz de la vista. active es la clave del ítem activo del menú (projects, milestones, payments…). menu reemplaza el menú real sólo para pantallas que Portal aún no tiene. Nada navega.

- `area`?: "home"|"organization"|"project"|"product"|null (null = por defecto)
- `audience`?: "client"|"staff"|null (null = por defecto)
- `active`?: string (≤80) (null = por defecto)
- `menu`?: [{ label?: string (min 1, ≤160) (null = por defecto), items: [{ key: string (min 1, ≤80), label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap" }] (min 1, máx 12) }] (min 1, máx 6) (null = por defecto)
- `organization`?: string (min 1, ≤160) (null = por defecto)
- `organizations`?: [string (min 1, ≤160)] (máx 20) (null = por defecto)
- `project`?: string (min 1, ≤160) (null = por defecto)
- `projects`?: [string (min 1, ≤160)] (máx 20) (null = por defecto)
- `breadcrumb`?: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 6) (null = por defecto)
- `user`: { name: string (min 1, ≤160), email: string (min 1, ≤160) }

Ejemplo: `{"area":"project","audience":"client","active":"milestones","organization":"Portenta","organizations":["Portenta","Grupo Lumen"],"project":"CRM comercial","projects":["CRM comercial","Portal de distribuidores"],"user":{"name":"Julio César Vega","email":"julio@portenta.mx"}}`

#### SiteShell (admite hijos)

Página del sitio público de Pai (pai.lat), idéntica a la real: header flotante con logo, menús Soluciones/Productos/Empresa, idiomas ES/EN/PT y «Hablemos de tu proyecto»; footer con columnas y banner de cookies. Sus hijos son las secciones (SiteHero, LogoGrid, SectionIntro, ServiceCards, CtaBand…). Va siempre como raíz. page marca la página del menú (home deja el header transparente sobre el hero; contact quita el botón). Nunca uses AppShell ni PortalShell para el sitio. Nada navega.

- `lang`?: "es"|"en"|"pt"|null (null = por defecto)
- `page`?: "home"|"services"|"industries"|"portal"|"about"|"manifesto"|"contact"|null (null = por defecto)
- `cookies`?: boolean (null = por defecto)

Ejemplo: `{"lang":"es","page":"home","cookies":true}`

### Grupo: Sitio web

#### ContactSection (admite hijos)

«Hablemos» del sitio en dos columnas: a la izquierda eyebrow, titular, texto y los pasos numerados de lo que pasa después (next los titula); a la derecha su hijo, el formulario (compuesto con Field, Input, Select, Textarea y Checkbox; nada se envía). Sin hijo, una tarjeta con los pasos, la llamada (cta) y su nota. variant page es la página de contacto (titular h1); close, el cierre de una página (h2, por defecto).

- `variant`?: "page"|"close"|null (null = por defecto)
- `eyebrow`: string (min 1, ≤160)
- `title`: string (min 1, ≤200)
- `body`: string (≤2000)
- `next`?: string (min 1, ≤160) (null = por defecto)
- `steps`: [{ title: string (min 1, ≤160), body: string (≤2000) }] (min 1, máx 5)
- `cta`?: string (min 1, ≤160) (null = por defecto)
- `note`?: string (≤2000) (null = por defecto)

Ejemplo: `{"variant":"close","eyebrow":"Hablemos","title":"Cuéntanos qué necesita tu operación","body":"Una conversación corta basta para saber si podemos ayudarte y cómo.","next":"Qué pasa después","steps":[{"title":"Leemos tu mensaje","body":"Una persona del equipo lo revisa, no un bot."},{"title":"Te proponemos una llamada","body":"Treinta minutos para entender el problema."},{"title":"Recibes una propuesta","body":"Alcance, tiempos e inversión por escrito."}],"cta":"Hablemos de tu proyecto","note":"Sin compromiso: si no somos la opción, te lo decimos."}`

#### CtaBand

Cierre de una página del sitio: titular grande, una línea de texto y dos llamadas (primary sólida en el color de marca, secondary con flecha). centered la centra.

- `headline`: string (min 1, ≤200)
- `description`?: string (≤2000) (null = por defecto)
- `primary`: string (min 1, ≤160)
- `secondary`?: string (min 1, ≤160) (null = por defecto)
- `centered`?: boolean (null = por defecto)

Ejemplo: `{"headline":"Hablemos de tu proyecto","description":"Te respondemos en 24 horas con los siguientes pasos.","primary":"Agenda una llamada","secondary":"Conoce nuestros servicios","centered":true}`

#### LogoGrid

Rejilla de logos de clientes de la home de pai.lat («Equipos que confían en Pai»): celdas con línea fina, 2, 4 u 8 por fila según el ancho. Cada logo se escribe como su nombre en tipografía de marca (la vista no carga imágenes).

- `kicker`?: string (min 1, ≤160) (null = por defecto)
- `logos`: [string (min 1, ≤40)] (min 2, máx 16)

Ejemplo: `{"kicker":"Equipos que confían en Pai","logos":["Stripe","Anthropic","Walmart Connect","Pedigree","Danup","Nestlé","LA Galaxy","KitKat"]}`

#### SectionIntro

Sección del sitio con titular grande a la izquierda y texto a la derecha (en móvil, uno bajo el otro), como las de la home de pai.lat. kicker es una etiqueta pequeña sobre el titular.

- `kicker`?: string (min 1, ≤160) (null = por defecto)
- `title`: string (min 1, ≤200)
- `body`: string (≤2000)

Ejemplo: `{"title":"El conocimiento y el método para construir con AI Agents","body":"Acompañamos a tu equipo con servicios de diseño e ingeniería, desde preparar el conocimiento del negocio hasta desarrollar, integrar y validar el producto."}`

#### ServiceCards

Tarjetas de servicios o capacidades del sitio (2 a 6), en 1, 2 o 3 columnas: icono, título, texto y una lista corta de lo que incluye.

- `items`: [{ title: string (min 1, ≤160), body: string (≤2000), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), points?: [string (min 1, ≤160)] (máx 6) (null = por defecto) }] (min 2, máx 6)

Ejemplo: `{"items":[{"title":"Diagnóstico","body":"Entendemos tu operación y lo que necesitas resolver.","icon":"search","points":["Entrevistas","Mapa de procesos"]},{"title":"Construcción por módulos","body":"Lo ves en pantallas y lo construimos por etapas.","icon":"layers","points":["Prototipos","Entregas quincenales"]},{"title":"Operación","body":"Operamos y mejoramos el producto con tu equipo.","icon":"settings"}]}`

#### SiteHero

Hero de la home de pai.lat, el real: fondo de puntos y malla de color animada a la derecha, sello opcional (badge, p. ej. «Stripe Premier Partner»), titular grande cuyo final (highlight) va en el degradado de marca, introducción y dos llamadas (primary sólida, secondary discreta). Primer hijo de SiteShell.

- `badge`?: string (min 1, ≤160) (null = por defecto)
- `title`: string (min 1, ≤200)
- `highlight`?: string (≤120) (null = por defecto)
- `intro`: string (≤2000)
- `primary`?: string (min 1, ≤160) (null = por defecto)
- `secondary`?: string (min 1, ≤160) (null = por defecto)

Ejemplo: `{"badge":"Stripe Premier Partner","title":"Hacemos simple lo complejo, ","highlight":"posible lo imposible.","intro":"Diseñamos, construimos y operamos productos digitales, pagos e IA para empresas y plataformas en México y Latinoamérica.","primary":"Hablemos de tu proyecto","secondary":"Explora cómo trabajamos"}`

### Grupo: Estructura

#### Accordion

Secciones desplegables de texto (preguntas frecuentes, detalles secundarios).

- `items`: [{ title: string (min 1, ≤160), content: string (≤2000) }] (min 1, máx 60)
- `type`?: "single"|"multiple"|null (null = por defecto)

Ejemplo: `{"items":[{"title":"¿Quién aprueba los entregables?","content":"La dirección del proyecto, en la revisión semanal."},{"title":"¿Cuándo se factura?","content":"Al cerrar cada hito."}],"type":"single"}`

#### Card (admite hijos)

Tarjeta con título y descripción opcionales que agrupa contenido relacionado. En su encabezado puede llevar una acción (botón; con href navega) y un menú «⋯» decorativo. No la uses como encabezado de la vista ni anides tarjetas dentro de tarjetas.

- `title`?: string (null = por defecto)
- `description`?: string (null = por defecto)
- `maxWidth`?: "sm"|"md"|"lg"|"full"|null (null = por defecto)
- `centered`?: boolean (null = por defecto)
- `action`?: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) } (null = por defecto)
- `menu`?: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), destructive?: boolean (null = por defecto), separatorBefore?: boolean (null = por defecto) }] (min 1, máx 20) (null = por defecto)

Ejemplo: `{"title":"Ventas por cerrar","description":"Oportunidades con fecha de cierre este mes.","action":{"label":"Ver todas","href":"/organization/projects"},"menu":[{"label":"Exportar","icon":"download"}]}`

#### Collapsible (admite hijos)

Una sección desplegable con título; sus hijos se muestran al abrirla.

- `title`: string
- `defaultOpen`?: boolean (null = por defecto)

Ejemplo: `{"title":"Detalle del cálculo","defaultOpen":true}`

#### DetailSheet (admite hijos)

Detalle de un elemento (un pago, una tarea, un hito) con la anatomía del panel lateral de Pai: antetítulo, título, estados, descripción, cuerpo (sus hijos: KeyValue, Text, Timeline…) y acciones al pie. presentation inline (por omisión) lo dibuja en la vista; overlay lo abre sobre la página con un botón (triggerLabel). Cerrar sólo lo oculta en la vista.

- `eyebrow`?: string (min 1, ≤160) (null = por defecto)
- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `badges`?: [{ label: string (min 1, ≤160), tone: "neutral"|"info"|"progress"|"success"|"warning"|"danger" }] (máx 4) (null = por defecto)
- `actions`?: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) }] (máx 3) (null = por defecto)
- `presentation`?: "inline"|"overlay"|null (null = por defecto)
- `open`?: boolean (null = por defecto)
- `triggerLabel`?: string (min 1, ≤160) (null = por defecto)
- `size`?: "md"|"lg"|null (null = por defecto)

Ejemplo: `{"eyebrow":"Pago · 2 de 3","title":"Anticipo de construcción","description":"USD 4,000.00 · Transferencia","badges":[{"label":"Pagado","tone":"success"}],"actions":[{"label":"Descargar factura","icon":"download"}]}`

#### Grid (admite hijos)

Cuadrícula de 1 a 6 columnas que se apila en pantallas angostas. Úsala para tarjetas de métricas (5 o 6 en una fila de KPIs) o grupos paralelos.

- `columns`?: integer (≥1, ≤6) (null = por defecto)
- `gap`?: "sm"|"md"|"lg"|"xl"|null (null = por defecto)

Ejemplo: `{"columns":3,"gap":"md"}`

#### Section (admite hijos)

Región con título (h2) y descripción opcional que agrupa los bloques de un tema de la vista.

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)

Ejemplo: `{"title":"Avance","description":"Estado al cierre de septiembre."}`

#### Separator

Línea divisoria entre bloques.

- `orientation`?: "horizontal"|"vertical"|null (null = por defecto)

Ejemplo: `{"orientation":"horizontal"}`

#### Stack (admite hijos)

Contenedor flex vertical u horizontal; la base de cualquier vista. Sus hijos se apilan con el espacio indicado.

- `direction`?: "horizontal"|"vertical"|null (null = por defecto)
- `gap`?: "none"|"sm"|"md"|"lg"|"xl"|null (null = por defecto)
- `align`?: "start"|"center"|"end"|"stretch"|null (null = por defecto)
- `justify`?: "start"|"center"|"end"|"between"|"around"|null (null = por defecto)

Ejemplo: `{"direction":"vertical","gap":"md"}`

#### Tabs (admite hijos)

Pestañas. Declara las pestañas en tabs y pon un hijo por pestaña, en el mismo orden (normalmente un Stack).

- `tabs`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 10)
- `defaultValue`?: string (null = por defecto)

Ejemplo: `{"tabs":[{"label":"Hitos","value":"hitos"},{"label":"Riesgos","value":"riesgos"}],"defaultValue":"hitos"}`

#### UnderlinedTabs (admite hijos)

Pestañas subrayadas, las de las secciones de un proyecto (Resumen, Cronograma, Pagos). Mismas props que Tabs (un hijo por pestaña, en orden) y variant: portal (por defecto) o console, la barra compacta pegada bajo la barra de página de Console.

- `tabs`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 10)
- `defaultValue`?: string (null = por defecto)
- `variant`?: "portal"|"console"|null (null = por defecto)

Ejemplo: `{"tabs":[{"label":"Resumen","value":"summary"},{"label":"Pagos","value":"payments"},{"label":"Archivos","value":"files"}],"defaultValue":"summary"}`

### Grupo: Contenido

#### Alert

Aviso destacado: info, success, warning o error. Úsalo para conclusiones, riesgos o advertencias. Sin title es un solo párrafo (message).

- `title`?: string (min 1) (null = por defecto)
- `message`?: string (null = por defecto)
- `type`?: "info"|"success"|"warning"|"error"|null (null = por defecto)

Ejemplo: `{"title":"Riesgo de retraso","message":"La integración con el ERP depende de credenciales del cliente.","type":"warning"}`

#### Avatar

Iniciales de una persona (sin imagen externa).

- `name`: string
- `size`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"name":"Julio César Vega","size":"md"}`

#### Badge

Etiqueta corta de estado o categoría.

- `text`: string
- `variant`?: "default"|"secondary"|"destructive"|"outline"|null (null = por defecto)

Ejemplo: `{"text":"En curso","variant":"secondary"}`

#### CommentsPanel

Comentarios de un documento (el panel del riel de Portal y Console): hilos del más nuevo al más viejo, cada uno con su visibilidad (client o internal), una cita opcional del texto comentado (quote) y sus respuestas; author con agent true se marca como agente. staff dibuja la vista del equipo. Escribir un comentario o una respuesta lo agrega en la vista; nada se envía.

- `threads`: [{ id: string (min 1, ≤80), visibility?: "client"|"internal"|null (null = por defecto), quote?: string (min 1, ≤400) (null = por defecto), comments: [{ id: string (min 1, ≤80), body: string (min 1, ≤2000), author: string (min 1, ≤160), agent?: boolean (null = por defecto), at: string }] (min 1, máx 30) }] (máx 30)
- `staff`?: boolean (null = por defecto)
- `canComment`?: boolean (null = por defecto)

Ejemplo: `{"threads":[{"id":"h1","visibility":"client","quote":"El anticipo se paga al firmar.","comments":[{"id":"c1","body":"¿Puede ser al iniciar la construcción?","author":"Marta Ruiz","at":"2026-10-02T16:20:00Z"},{"id":"c2","body":"Sí: lo movemos al hito 2.","author":"Luis Pérez","at":"2026-10-02T17:05:00Z"}]}]}`

#### Heading

Título de una parte de la vista. h1 sólo para el título principal; luego h2 y h3.

- `text`: string
- `level`?: "h1"|"h2"|"h3"|"h4"|null (null = por defecto)

Ejemplo: `{"text":"Estado del proyecto","level":"h1"}`

#### HistoryPanel

Historial de versiones de un documento (el panel del riel de Portal y Console), de la más nueva a la más vieja: revisión, resumen del cambio, tipo (create, edit, import, restore, revision, send, accept, reject), autor (agent true lo marca como agente) y fecha; current marca la versión vigente. Sólo lectura.

- `entries`: [{ id: string (min 1, ≤80), revision?: integer (≥1, ≤9007199254740991) (null = por defecto), summary: string (min 1, ≤300), kind?: "create"|"edit"|"import"|"restore"|"revision"|"send"|"accept"|"reject"|null (null = por defecto), author: string (min 1, ≤160), agent?: boolean (null = por defecto), at: string, current?: boolean (null = por defecto) }] (máx 50)
- `emptyLabel`?: string (min 1, ≤160) (null = por defecto)

Ejemplo: `{"entries":[{"id":"v3","revision":3,"summary":"Mueve el anticipo al hito 2","kind":"edit","author":"Luis Pérez","at":"2026-10-02T17:10:00Z","current":true},{"id":"v2","revision":2,"summary":"Agrega el cronograma de pagos","kind":"edit","author":"Agente","agent":true,"at":"2026-09-28T10:00:00Z"},{"id":"v1","revision":1,"summary":"Primera versión","kind":"create","author":"Luis Pérez","at":"2026-09-27T09:30:00Z"}]}`

#### Item

Fila de una lista (archivo, persona, integración): icono, título, descripción y un dato a la derecha. Con href toda la fila es un enlace. Apila varios en un Stack con gap sm.

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `meta`?: string (min 1, ≤160) (null = por defecto)
- `href`?: string (null = por defecto)
- `variant`?: "default"|"outline"|"muted"|null (null = por defecto)

Ejemplo: `{"title":"Contrato marco.pdf","description":"Subido por Ana López","icon":"file","meta":"2.4 MB","variant":"outline"}`

#### Kbd

Atajo de teclado («⌘ K», «Ctrl Enter»): una tecla por elemento de keys.

- `keys`: [string (min 1, ≤12)] (min 1, máx 4)

Ejemplo: `{"keys":["⌘","K"]}`

#### Link

Enlace a una ruta del Portal (/organization/projects/…) o a un sitio https.

- `label`: string (min 1, ≤160)
- `href`: string

Ejemplo: `{"label":"Ver el cronograma","href":"/organization/projects"}`

#### List

Lista de viñetas o numerada de texto plano.

- `items`: [string (min 1, ≤640)] (min 1, máx 60)
- `ordered`?: boolean (null = por defecto)

Ejemplo: `{"items":["Validar el alcance","Firmar la propuesta","Agendar el arranque"],"ordered":true}`

#### StatusBadge

Estado con el tono de Pai (neutral, info, progress, success, warning, danger), como en las tablas de proyectos, pagos y propuestas. El texto dice el estado; el tono sólo lo refuerza.

- `label`: string (min 1, ≤160)
- `tone`: "neutral"|"info"|"progress"|"success"|"warning"|"danger"

Ejemplo: `{"label":"Pagado","tone":"success"}`

#### StatusDot

Punto de color con su texto: el estado discreto de una fila o un hito (neutral, info, progress, success, warning, danger).

- `label`: string (min 1, ≤160)
- `tone`: "neutral"|"info"|"progress"|"success"|"warning"|"danger"

Ejemplo: `{"label":"En curso","tone":"progress"}`

#### Text

Párrafo de texto plano (sin Markdown). Variantes: body, lead (introducción), muted, caption, code. tone lo colorea para una nota breve: success, warning, danger o info.

- `text`: string
- `variant`?: "body"|"caption"|"muted"|"lead"|"code"|null (null = por defecto)
- `tone`?: "success"|"warning"|"danger"|"info"|null (null = por defecto)

Ejemplo: `{"text":"Resumen al cierre de la semana, preparado por el agente.","variant":"lead"}`

#### Tooltip (admite hijos)

Muestra un texto breve al pasar el cursor o enfocar su único hijo, que no debe ser interactivo (Text, Badge, StatusBadge, Kbd): la ayuda de un dato.

- `text`: string (min 1, ≤160)

Ejemplo: `{"text":"Monto con IVA incluido"}`

### Grupo: Datos

#### BarList

Lista de barras horizontales con su porcentaje (ventas por vendedor, avance por área). Cada barra se mide contra max, o contra la mayor si no hay max; display reemplaza el número mostrado («$1.2 M»).

- `items`: [{ label: string (min 1, ≤160), value: number (≥0), display?: string (≤40) (null = por defecto) }] (min 1, máx 60)
- `max`?: number (null = por defecto)
- `showPercent`?: boolean (null = por defecto)

Ejemplo: `{"items":[{"label":"Norte","value":82,"display":"$4.1 M"},{"label":"Centro","value":64,"display":"$3.2 M"},{"label":"Sur","value":31,"display":"$1.6 M"}],"max":100,"showPercent":true}`

#### Chart

Gráfica con los colores del tema: bar, line, area o pie. categories es el eje X (o las porciones de pie) y cada serie trae un valor por categoría. pie usa una sola serie. Con kind bar, orientation horizontal dibuja barras acostadas (rankings, etiquetas largas).

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `kind`: "bar"|"line"|"area"|"pie"
- `categories`: [string (min 1, ≤80)] (min 1, máx 60)
- `series`: [{ name: string (min 1, ≤80), values: [number] }] (min 1, máx 6)
- `unit`?: string (≤20) (null = por defecto)
- `stacked`?: boolean (null = por defecto)
- `orientation`?: "vertical"|"horizontal"|null (null = por defecto)

Ejemplo: `{"title":"Horas por mes","kind":"bar","categories":["Jul","Ago","Sep"],"series":[{"name":"Horas","values":[120,140,98]}],"unit":"h"}`

#### DataTable

La tabla de datos de Portal y Console (DataTable): columnas tipadas (text, number, money en centavos alineado a la derecha, percent, date, badge, status con tono, link, person, progress), buscador, filtros «Etiqueta: valor», orden por columna, paginación (pageSize; null la oculta y muestra todas las filas), selección (selectable añade casillas; selectionSummary deja sólo el pie «0 de N fila(s) seleccionada(s)», como la lista de proyectos), filas apagadas (muted) y un menú «⋯» por fila. Todo funciona dentro de la vista (filtra, ordena, pagina) y nada se guarda ni navega. Cada fila trae id y cells: { [key de columna]: valor }; una celda vacía es null.

- `columns`: [{ key: string, header: string (min 1, ≤160), sortable?: boolean (null = por defecto), hideBelow?: "sm"|"md"|"lg"|null (null = por defecto), type: "text"|"number"|"money"|"percent"|"date"|"badge"|"status"|"link"|"person"|"progress", secondaryKey?: string (null = por defecto), decimals?: integer (≥0, ≤4) (null = por defecto), currency?: string (min 3, ≤3) (null = por defecto), plusTax?: boolean (null = por defecto), format?: "day"|"instant"|"relative"|null (null = por defecto) }] (min 1, máx 10)
- `rows`: [{ id: string (min 1, ≤80), cells: object, muted?: boolean (null = por defecto), actions?: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), destructive?: boolean (null = por defecto), separatorBefore?: boolean (null = por defecto) }] (min 1, máx 20) (null = por defecto) }] (máx 200)
- `search`?: string (min 1, ≤160) (null = por defecto)
- `filters`?: [{ key: string, title: string (min 1, ≤160), options?: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (máx 20) (null = por defecto) }] (máx 4) (null = por defecto)
- `defaultSort`?: { key: string, desc: boolean } (null = por defecto)
- `pageSize`?: number | number | number | number | number | number (null = por defecto)
- `selectable`?: boolean (null = por defecto)
- `selectionSummary`?: boolean (null = por defecto)
- `empty`?: { title: string (min 1, ≤160), description?: string (≤2000) (null = por defecto), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto) } (null = por defecto)
- `toolbarAction`?: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) } (null = por defecto)

Ejemplo: `{"columns":[{"key":"client","header":"Cliente","type":"text","secondaryKey":"city","sortable":true},{"key":"seller","header":"Vendedor","type":"person","hideBelow":"md"},{"key":"stage","header":"Etapa","type":"status","sortable":true},{"key":"amount","header":"Monto","type":"money","currency":"MXN","sortable":true},{"key":"close","header":"Cierre","type":"date","hideBelow":"sm","sortable":true}],"rows":[{"id":"v1","cells":{"client":"Grupo Lumen","city":"Monterrey","seller":{"name":"Ana López","secondary":"Norte"},"stage":{"label":"Negociación","tone":"progress"},"amount":42000000,"close":"2026-10-28"},"actions":[{"label":"Ver detalle"},{"label":"Marcar como ganada","icon":"check"}]},{"id":"v2","cells":{"client":"Ñandú Logística","city":"Querétaro","seller":{"name":"Luis Pérez","secondary":"Centro"},"stage":{"label":"Propuesta enviada","tone":"info"},"amount":18500000,"close":"2026-11-15"}},{"id":"v3","cells":{"client":"Constructora Alba","city":"Puebla","seller":{"name":"Ana López","secondary":"Norte"},"stage":{"label":"Perdida","tone":"danger"},"amount":9900000,"close":"2026-09-30"},"muted":true}],"search":"Buscar cliente…","filters":[{"key":"stage","title":"Etapa"}],"defaultSort":{"key":"amount","desc":true},"pageSize":10,"selectable":false,"empty":{"title":"Aún no hay ventas","icon":"receipt"},"toolbarAction":{"label":"Nueva venta","icon":"plus"}}`

#### KeyValue

Pares etiqueta–valor (fechas, responsables, montos) en 1 a 3 columnas.

- `items`: [{ label: string (min 1, ≤160), value: string (min 1, ≤400) }] (min 1, máx 60)
- `columns`?: integer (≥1, ≤3) (null = por defecto)

Ejemplo: `{"items":[{"label":"Responsable","value":"Ana López"},{"label":"Inicio","value":"1 de septiembre de 2026"},{"label":"Presupuesto","value":"$420,000 MXN"}],"columns":3}`

#### Metric

Indicador (KPI): etiqueta, valor ya formateado («68 %», «$1.2 M»), unidad pequeña opcional («MXN») y detalle con su comparación o fecha de corte. tone colorea el valor: positive, warning, negative o info.

- `label`: string (min 1, ≤160)
- `value`: string (min 1, ≤40)
- `detail`?: string (≤160) (null = por defecto)
- `trend`?: "up"|"down"|"flat"|null (null = por defecto)
- `unit`?: string (min 1, ≤12) (null = por defecto)
- `tone`?: "neutral"|"positive"|"warning"|"negative"|"info"|null (null = por defecto)

Ejemplo: `{"label":"Avance","value":"68 %","detail":"+12 pts vs. agosto","trend":"up","tone":"positive"}`

#### Progress

Barra de avance de 0 a 100 con etiqueta opcional.

- `value`: number
- `max`?: number (null = por defecto)
- `label`?: string (null = por defecto)

Ejemplo: `{"value":68,"label":"Avance del proyecto"}`

#### Table

Tabla de datos: columns son los encabezados y rows un arreglo de filas con una celda por columna.

- `columns`: [string (min 1, ≤160)] (min 1, máx 10)
- `rows`: [[string (≤640)]] (máx 200)
- `caption`?: string (≤160) (null = por defecto)

Ejemplo: `{"columns":["Hito","Responsable","Fecha"],"rows":[["Diseño","Ana López","12 sep"],["Desarrollo","Luis Pérez","30 oct"]],"caption":"Hitos del trimestre"}`

### Grupo: Controles

#### ActionMenu

Menú de acciones que se abre al pulsar: sin label es el botón «⋯» de las filas y tarjetas; con label es un botón con flecha. Sus opciones son decorativas (no ejecutan nada).

- `label`?: string (min 1, ≤160) (null = por defecto)
- `items`: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), destructive?: boolean (null = por defecto), separatorBefore?: boolean (null = por defecto) }] (min 1, máx 20)
- `align`?: "start"|"end"|null (null = por defecto)

Ejemplo: `{"items":[{"label":"Editar","icon":"pencil"},{"label":"Duplicar","icon":"copy"},{"label":"Eliminar","icon":"trash","destructive":true,"separatorBefore":true}],"align":"end"}`

#### Button

Botón con las variantes de Pai. Con href navega (ruta del Portal o https); sin href es decorativo: se ve y se pulsa, pero no hace nada. iconOnly deja sólo el icono (label queda como nombre accesible).

- `label`: string (min 1, ≤160)
- `variant`?: "default"|"secondary"|"outline"|"ghost"|"destructive"|"link"|null (null = por defecto)
- `size`?: "sm"|"default"|"lg"|null (null = por defecto)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `iconOnly`?: boolean (null = por defecto)
- `href`?: string (null = por defecto)
- `disabled`?: boolean (null = por defecto)

Ejemplo: `{"label":"Nueva venta","variant":"default","icon":"plus"}`

#### ButtonGroup (admite hijos)

Agrupa botones relacionados (Button, ActionMenu) pegados entre sí, como «Exportar | ⋯».

- `orientation`?: "horizontal"|"vertical"|null (null = por defecto)

Ejemplo: `{"orientation":"horizontal"}`

#### Calendar

Calendario de un mes con fechas marcadas (entregas, reuniones). selected son fechas AAAA-MM-DD; con mode range son el inicio y el fin. Se puede cambiar de mes y elegir dentro de la vista; nada se guarda.

- `month`?: string (null = por defecto)
- `selected`?: [string] (máx 31) (null = por defecto)
- `mode`?: "single"|"multiple"|"range"|null (null = por defecto)

Ejemplo: `{"month":"2026-10","selected":["2026-10-12","2026-10-16"],"mode":"range"}`

#### Checkbox

Casilla con su etiqueta (aceptar términos, marcar una opción). Se marca y desmarca dentro de la vista; nada se guarda.

- `label`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `checked`?: boolean (null = por defecto)
- `disabled`?: boolean (null = por defecto)

Ejemplo: `{"label":"Acepto los términos de la propuesta","checked":true}`

#### Command

Buscador de comandos (paleta tipo ⌘K) con grupos de opciones y atajos. Filtra al escribir dentro de la vista; las opciones no ejecutan nada.

- `placeholder`?: string (min 1, ≤160) (null = por defecto)
- `groups`: [{ heading?: string (min 1, ≤160) (null = por defecto), items: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), shortcut?: string (≤20) (null = por defecto) }] (min 1, máx 20) }] (min 1, máx 6)
- `empty`?: string (min 1, ≤160) (null = por defecto)

Ejemplo: `{"placeholder":"Busca un proyecto o una acción…","groups":[{"heading":"Acciones","items":[{"label":"Nueva propuesta","icon":"file-signature","shortcut":"⌘N"},{"label":"Subir archivo","icon":"upload"}]},{"heading":"Ir a","items":[{"label":"Cronograma","icon":"calendar"},{"label":"Pagos","icon":"wallet"}]}]}`

#### Dropzone

Zona para arrastrar o elegir archivos (decorativa: no sube nada). accept dice qué se admite («PDF o XML, hasta 10 MB»).

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `accept`?: string (≤120) (null = por defecto)
- `button`?: string (min 1, ≤160) (null = por defecto)

Ejemplo: `{"title":"Arrastra aquí la factura","description":"O elígela desde tu equipo.","accept":"PDF o XML, hasta 10 MB","button":"Elegir archivo"}`

#### FilterBar

Barra de filtros sobre una tabla o tablero: buscador opcional, filtros «Etiqueta: valor» (listas que cambian dentro de la vista, sin filtrar nada) y un botón principal a la derecha.

- `search`?: string (min 1, ≤160) (null = por defecto)
- `filters`: [{ label: string (min 1, ≤40), value: string (min 1, ≤80), options?: [string (min 1, ≤80)] (máx 20) (null = por defecto) }] (máx 6)
- `action`?: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) } (null = por defecto)

Ejemplo: `{"search":"Buscar cliente…","filters":[{"label":"Vendedor","value":"Todos","options":["Todos","Ana López","Luis Pérez"]},{"label":"Periodo","value":"Octubre 2026"}],"action":{"label":"Nueva venta","icon":"plus"}}`

#### Input

Campo de texto de una línea con etiqueta y ayuda opcionales. Se puede escribir en él, pero nada se envía ni se guarda.

- `label`?: string (min 1, ≤160) (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)
- `disabled`?: boolean (null = por defecto)
- `placeholder`?: string (min 1, ≤160) (null = por defecto)
- `value`?: string (≤400) (null = por defecto)
- `type`?: "text"|"email"|"number"|"search"|"tel"|"url"|null (null = por defecto)

Ejemplo: `{"label":"Correo del cliente","placeholder":"nombre@empresa.com","type":"email","description":"Le enviaremos la propuesta a esta dirección."}`

#### RadioGroup

Opciones excluyentes visibles a la vez (2 a 6), con etiqueta. Cambia dentro de la vista; nada se guarda.

- `label`?: string (min 1, ≤160) (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)
- `disabled`?: boolean (null = por defecto)
- `options`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 6)
- `value`?: string (null = por defecto)

Ejemplo: `{"label":"Forma de pago","options":[{"label":"Transferencia","value":"transfer"},{"label":"Tarjeta","value":"card"}],"value":"transfer"}`

#### Select

Lista desplegable para elegir una opción. Se abre y cambia dentro de la vista; nada se guarda. value es la opción elegida al cargar.

- `label`?: string (min 1, ≤160) (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)
- `disabled`?: boolean (null = por defecto)
- `placeholder`?: string (min 1, ≤160) (null = por defecto)
- `options`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 1, máx 60)
- `value`?: string (null = por defecto)

Ejemplo: `{"label":"Etapa","options":[{"label":"Prospecto","value":"prospect"},{"label":"Negociación","value":"negotiation"},{"label":"Cerrada","value":"closed"}],"value":"negotiation"}`

#### Switch

Interruptor de encendido/apagado con su etiqueta (preferencias, avisos). Cambia dentro de la vista; nada se guarda.

- `label`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `checked`?: boolean (null = por defecto)
- `disabled`?: boolean (null = por defecto)

Ejemplo: `{"label":"Avisarme por correo","description":"Un resumen cada lunes.","checked":true}`

#### Textarea

Campo de texto de varias líneas (comentarios, notas). Se puede escribir, pero nada se envía.

- `label`?: string (min 1, ≤160) (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)
- `disabled`?: boolean (null = por defecto)
- `placeholder`?: string (min 1, ≤160) (null = por defecto)
- `value`?: string (≤2000) (null = por defecto)
- `rows`?: integer (≥2, ≤12) (null = por defecto)

Ejemplo: `{"label":"Notas para el equipo","placeholder":"Escribe un comentario…","rows":3}`

#### ToggleGroup

Botones segmentados para cambiar de modo (Lista | Tablero, Semana | Mes). Cambia dentro de la vista; no cambia el contenido ni navega.

- `options`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto) }] (min 2, máx 6)
- `value`?: string (null = por defecto)
- `variant`?: "default"|"outline"|null (null = por defecto)

Ejemplo: `{"options":[{"label":"Lista","value":"list"},{"label":"Tablero","value":"board"}],"value":"list","variant":"outline"}`

### Grupo: Navegación

#### Breadcrumb

Migas de pan: dónde está la pantalla («Proyectos › Portenta › Cronograma»). El último elemento es la página actual; los anteriores pueden llevar href.

- `items`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 8)

Ejemplo: `{"items":[{"label":"Proyectos","href":"/organization/projects"},{"label":"Portenta"},{"label":"Cronograma"}]}`

#### OrgSwitcher

El selector de organización de Portal, solo: muestra la organización (o Pai sin organization) y se abre con «Buscar…», Pai, Consola (staff) y «Tus organizaciones». Filtra al escribir; elegir no cambia nada.

- `organization`?: string (min 1, ≤160) (null = por defecto)
- `organizations`?: [string (min 1, ≤160)] (máx 20) (null = por defecto)
- `staff`?: boolean (null = por defecto)

Ejemplo: `{"organization":"Portenta","organizations":["Portenta","Grupo Lumen","Ñandú Logística"],"staff":true}`

#### PageBar

La barra superior de una página de Portal o Console, sola: botón del menú lateral, migas, acciones a la derecha (botones decorativos) y, si assistant, «Preguntar al agente». Úsala para mostrar la barra fuera de un PortalShell/ConsoleShell (que ya la traen).

- `breadcrumb`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 6)
- `actions`?: [string (min 1, ≤160)] (máx 3) (null = por defecto)
- `assistant`?: boolean (null = por defecto)

Ejemplo: `{"breadcrumb":[{"label":"Proyectos","href":"/organization/projects"},{"label":"CRM comercial"}],"actions":["Exportar"],"assistant":true}`

#### Pagination

Paginación bajo una tabla o lista: página actual de un total. Se puede cambiar de página dentro de la vista, pero el contenido no cambia.

- `page`: integer (≥1, ≤9007199254740991)
- `pages`: integer (≥1, ≤999)

Ejemplo: `{"page":2,"pages":8}`

#### ProjectHeader

Cabecera de un proyecto de Portal (Inicio, Cronograma, Pagos…): nombre, estado (draft, planned, active, on_hold, completed, cancelled), arquitecto de Pai, fechas ya formateadas («28 jul – 18 ago») y la salud declarada (on_track, at_risk, off_track). compact es la versión de la barra del Cronograma.

- `name`: string (min 1, ≤160)
- `status`: "draft"|"planned"|"active"|"on_hold"|"completed"|"cancelled"
- `architect`?: string (min 1, ≤160) (null = por defecto)
- `dates`?: string (≤60) (null = por defecto)
- `health`?: "on_track"|"at_risk"|"off_track"|null (null = por defecto)
- `compact`?: boolean (null = por defecto)

Ejemplo: `{"name":"CRM comercial","status":"active","architect":"Ana López","dates":"1 sep – 30 nov","health":"at_risk"}`

#### ProjectSwitcher

El selector de proyecto de las migas de Portal: el nombre del proyecto con ⌃⌄ que abre la lista buscable de projects. Elegir no navega.

- `project`: string (min 1, ≤160)
- `projects`?: [string (min 1, ≤160)] (máx 30) (null = por defecto)

Ejemplo: `{"project":"CRM comercial","projects":["CRM comercial","Portal de distribuidores","App de ventas"]}`

### Grupo: Estados

#### EmptyState

Estado vacío de una sección, como en Portal: icono, «Aún no hay {objetos}», una línea para quien mira y una acción opcional (botón con href o decorativo).

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `action`?: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) } (null = por defecto)

Ejemplo: `{"title":"Aún no hay propuestas","description":"Cuando el equipo envíe una propuesta, aparecerá aquí.","icon":"file-signature","action":{"label":"Nueva propuesta","icon":"plus"}}`

#### ErrorState

Error al cargar una sección, como en Portal: «No se pudo cargar {X}.», una explicación opcional y el botón «Reintentar» (decorativo).

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `retry`?: boolean (null = por defecto)

Ejemplo: `{"title":"No se pudieron cargar los pagos.","description":"Revisa tu conexión e inténtalo de nuevo.","retry":true}`

#### LoadingState

Sección cargando, como en Portal: anuncia «Cargando {sección}» a los lectores de pantalla y muestra un esqueleto con la forma del contenido (text, list, card o table).

- `label`: string (min 1, ≤160)
- `shape`?: "text"|"list"|"card"|"table"|null (null = por defecto)
- `rows`?: integer (≥1, ≤12) (null = por defecto)

Ejemplo: `{"label":"Cargando pagos","shape":"table","rows":4}`

#### Skeleton

Bloques grises con la forma del contenido que aún no llega: text (líneas), list (filas con avatar), card (tarjeta) o table (filas de tabla).

- `shape`?: "text"|"list"|"card"|"table"|null (null = por defecto)
- `rows`?: integer (≥1, ≤12) (null = por defecto)

Ejemplo: `{"shape":"list","rows":3}`

#### Spinner

Indicador de actividad en curso (enviando, procesando) con un texto opcional al lado.

- `label`?: string (min 1, ≤160) (null = por defecto)

Ejemplo: `{"label":"Generando la propuesta…"}`

### Grupo: Planeación

#### Checklist

Lista de verificación (documentos de un expediente, requisitos): cada punto done (Validado), pending (Pendiente) o warning (Con observaciones), con un detalle opcional. label cambia la etiqueta del estado si hace falta («Recibido»).

- `items`: [{ label: string (min 1, ≤160), status: "done"|"pending"|"warning", detail?: string (≤160) (null = por defecto), statusLabel?: string (min 1, ≤40) (null = por defecto) }] (min 1, máx 40)

Ejemplo: `{"items":[{"label":"Identificación oficial","status":"done"},{"label":"Comprobante de domicilio","status":"warning","detail":"Tiene más de tres meses."},{"label":"Constancia de situación fiscal","status":"pending"}]}`

#### Kanban

Tablero Kanban genérico (el de Tareas de Pai, sin su dominio): columnas con su contador y tarjetas con título, descripción, etiquetas, responsable y fecha. Con interactive (por omisión true) las tarjetas se arrastran entre columnas dentro de la vista; nada se guarda. Para las tareas de un proyecto usa TaskBoard.

- `columns`: [{ id: string (min 1, ≤80), title: string (min 1, ≤160), tone?: "neutral"|"info"|"progress"|"success"|"warning"|"danger"|null (null = por defecto) }] (min 1, máx 8)
- `cards`: [{ id: string (min 1, ≤80), column: string (min 1, ≤80), title: string (min 1, ≤160), description?: string (≤2000) (null = por defecto), badges?: [{ label: string (min 1, ≤160), tone?: "neutral"|"info"|"progress"|"success"|"warning"|"danger"|null (null = por defecto) }] (máx 4) (null = por defecto), owner?: string (min 1, ≤160) (null = por defecto), due?: string (null = por defecto) }] (máx 200)
- `interactive`?: boolean (null = por defecto)

Ejemplo: `{"columns":[{"id":"lead","title":"Prospecto"},{"id":"proposal","title":"Propuesta","tone":"info"},{"id":"won","title":"Ganado","tone":"success"}],"cards":[{"id":"c1","column":"lead","title":"Distribuidora del Norte","description":"Pidió demo del portal de pedidos.","owner":"Ana López"},{"id":"c2","column":"proposal","title":"Clínica Santa Fe","badges":[{"label":"Prioridad","tone":"warning"}],"owner":"Luis Pérez","due":"2026-10-16"},{"id":"c3","column":"won","title":"Grupo Altamira","badges":[{"label":"Firmado","tone":"success"}]}]}`

#### MilestoneGanttLegend

Leyenda del Cronograma de Portal: colores de estado de los hitos (pendiente, en curso, completado, vencido) y, si se indican, barras, puntos, tareas, dependencias y línea base.

- `ranges`?: boolean (null = por defecto)
- `points`?: boolean (null = por defecto)
- `tasks`?: boolean (null = por defecto)
- `dependencies`?: boolean (null = por defecto)
- `baseline`?: boolean (null = por defecto)

Ejemplo: `{"ranges":true,"points":true,"tasks":true,"dependencies":true}`

#### MilestoneGanttSkeleton

Cronograma de Portal cargando: barra de navegación, árbol de hitos y barras del Gantt en gris. Para mostrar cómo se ve la pantalla mientras llegan los datos.


Ejemplo: `{}`

#### MilestoneTimeline

El Cronograma real de Portal: hitos como barras en el tiempo (con avance, responsable, monto y estado de pago), sus tareas, dependencias y línea base, y el panel de detalle al elegir uno. Se puede cambiar la escala, el zoom y las columnas, y abrir hitos y tareas; nada se guarda ni navega. Fechas AAAA-MM-DD; today fija el día de hoy (por defecto, el actual). selected abre un hito al cargar. staff es el de Console: «Nuevo hito» en la barra y los botones de editar y eliminar del detalle, inertes. framed:false lo dibuja sin marco, como en Portal.

- `milestones`: [{ id: string (min 1, ≤80), name: string (min 1, ≤160), start?: string (null = por defecto), end?: string (null = por defecto), status?: "pending"|"in_progress"|"completed"|null (null = por defecto), progress?: { done: integer (≥0, ≤9007199254740991), total: integer (≥0, ≤9007199254740991) } (null = por defecto), owner?: string (min 1, ≤160) (null = por defecto), amount?: number (≥0) (null = por defecto), currency?: string (min 3, ≤3) (null = por defecto), paymentStatus?: "unpaid"|"pending"|"paid"|null (null = por defecto), description?: string (≤2000) (null = por defecto), acceptanceCriteria?: string (≤2000) (null = por defecto), dependsOn?: [string (min 1, ≤80)] (máx 20) (null = por defecto), baseline?: { start: string, end: string } (null = por defecto), tasks?: [{ id: string (min 1, ≤80), title: string (min 1, ≤160), start?: string (null = por defecto), due?: string (null = por defecto), status?: "todo"|"doing"|"done"|"cancelled"|null (null = por defecto), owner?: string (min 1, ≤160) (null = por defecto), summary?: string (≤2000) (null = por defecto), dependsOn?: [string (min 1, ≤80)] (máx 20) (null = por defecto) }] (máx 60) (null = por defecto) }] (min 1, máx 60)
- `today`?: string (null = por defecto)
- `scale`?: "week"|"month"|"quarter"|"year"|null (null = por defecto)
- `zoom`?: number (≥0.5, ≤3) (null = por defecto)
- `columns`?: ["status"|"date"|"payment"|"owner"|"dependencies"] (máx 5) (null = por defecto)
- `selected`?: string (min 1, ≤80) (null = por defecto)
- `height`?: "sm"|"md"|"lg"|null (null = por defecto)
- `staff`?: boolean (null = por defecto)
- `framed`?: boolean (null = por defecto)

Ejemplo: `{"today":"2026-10-07","scale":"month","columns":["status","date","payment"],"milestones":[{"id":"descubrimiento","name":"Descubrimiento","start":"2026-09-01","end":"2026-09-26","status":"completed","owner":"Ana López","amount":120000,"currency":"MXN","paymentStatus":"paid","tasks":[{"id":"t1","title":"Entrevistas","start":"2026-09-01","due":"2026-09-10","status":"done"},{"id":"t2","title":"Mapa de procesos","start":"2026-09-10","due":"2026-09-24","status":"done","dependsOn":["t1"]}]},{"id":"construccion","name":"Construcción del CRM","start":"2026-09-28","end":"2026-11-20","status":"in_progress","owner":"Luis Pérez","amount":380000,"currency":"MXN","paymentStatus":"pending","dependsOn":["descubrimiento"],"baseline":{"start":"2026-09-28","end":"2026-11-13"},"tasks":[{"id":"t3","title":"Pipeline de ventas","start":"2026-09-28","due":"2026-10-16","status":"doing","owner":"Luis Pérez"},{"id":"t4","title":"Reportes","start":"2026-10-19","due":"2026-11-13","status":"todo","dependsOn":["t3"]}]},{"id":"salida","name":"Salida a producción","start":"2026-11-23","end":"2026-11-30","status":"pending","amount":100000,"currency":"MXN","paymentStatus":"unpaid","dependsOn":["construccion"]}]}`

#### Stages

Etapas de un proceso en una línea horizontal (Prospecto › Propuesta › Negociación › Cierre): cada una done, current o upcoming, con un detalle breve opcional (fecha, responsable).

- `items`: [{ label: string (min 1, ≤160), status: "done"|"current"|"upcoming", detail?: string (≤80) (null = por defecto) }] (min 2, máx 8)

Ejemplo: `{"items":[{"label":"Prospecto","status":"done","detail":"2 sep"},{"label":"Propuesta","status":"done","detail":"15 sep"},{"label":"Negociación","status":"current","detail":"En curso"},{"label":"Cierre","status":"upcoming"}]}`

#### TaskBoard

El tablero de Tareas real (staff de Pai): cuatro columnas fijas (Borrador, Por hacer, Hecha, Descartada) según status (draft o proposed → Borrador; active → Por hacer; resolved con outcome done → Hecha, wont_do → Descartada; rejected → Descartada), con buscador y filtro por hito, tarjetas con responsable, fechas y hito, y la ficha de la tarea al abrirla. Con interactive se arrastran las tarjetas entre columnas (con el diálogo de evidencia al cerrarla); todo pasa en la memoria de la vista, nada se guarda ni navega.

- `tasks`: [{ id: string (min 1, ≤80), title: string (min 1, ≤160), status: "draft"|"proposed"|"active"|"resolved"|"rejected", outcome?: "done"|"wont_do"|null (null = por defecto), owner?: string (min 1, ≤160) (null = por defecto), start?: string (null = por defecto), due?: string (null = por defecto), milestoneId?: string (min 1, ≤80) (null = por defecto), summary?: string (≤2000) (null = por defecto), visibility?: "internal"|"client"|null (null = por defecto) }] (máx 60)
- `milestones`?: [{ id: string (min 1, ≤80), name: string (min 1, ≤160) }] (máx 60) (null = por defecto)
- `today`?: string (null = por defecto)
- `interactive`?: boolean (null = por defecto)
- `search`?: string (min 1, ≤160) (null = por defecto)
- `milestoneId`?: string (min 1, ≤80) (null = por defecto)
- `openTaskId`?: string (min 1, ≤80) (null = por defecto)

Ejemplo: `{"today":"2026-10-07","interactive":true,"milestones":[{"id":"m1","name":"Descubrimiento"},{"id":"m2","name":"Construcción del CRM"}],"tasks":[{"id":"t1","title":"Definir etapas del pipeline","status":"proposed","milestoneId":"m2"},{"id":"t2","title":"Pantalla de oportunidades","status":"active","owner":"Luis Pérez","start":"2026-10-01","due":"2026-10-16","milestoneId":"m2"},{"id":"t3","title":"Importar clientes del ERP","status":"active","owner":"Ana López","due":"2026-10-03","milestoneId":"m2"},{"id":"t4","title":"Entrevistas con ventas","status":"resolved","outcome":"done","owner":"Ana López","due":"2026-09-10","milestoneId":"m1"},{"id":"t5","title":"App móvil","status":"rejected","summary":"Fuera del alcance de esta etapa."}]}`

#### Timeline

Cronología de hitos o eventos con fecha, título, descripción y estado (done, current, upcoming).

- `items`: [{ date: string (min 1, ≤40), title: string (min 1, ≤160), description?: string (≤2000) (null = por defecto), status?: "done"|"current"|"upcoming"|null (null = por defecto) }] (min 1, máx 60)

Ejemplo: `{"items":[{"date":"1 sep","title":"Arranque","status":"done"},{"date":"30 sep","title":"Diseño aprobado","description":"Revisión con dirección comercial.","status":"current"},{"date":"30 oct","title":"Salida a producción","status":"upcoming"}]}`

### Grupo: Proyecto

#### ActivityFeed

La actividad de un proyecto por día («Hoy», «Ayer», fecha), con un icono por tipo y la frase real («Ana publicó Alcance», «Se completó Descubrimiento»); las ráfagas de documentos del mismo autor y día se pliegan en «N documentos». variant recent es «Actividad reciente» del Inicio del Portal; log es «Actividad» de Console, con filtro por tipo y «Ver los N». at es un día (AAAA-MM-DD, hitos) o un instante; today fija el día de hoy (por defecto, el actual en Ciudad de México). Usa lo que devolvió project_activity.

- `events`: [{ id: string (min 1, ≤80), kind: "page_published"|"page_updated"|"proposal_sent"|"proposal_accepted"|"proposal_rejected"|"milestone_started"|"milestone_completed"|"status_update", at: string, subject: string (min 1, ≤160), actor?: string (min 1, ≤160) (null = por defecto), href?: string (null = por defecto) }] (máx 200)
- `variant`?: "recent"|"log"|null (null = por defecto)
- `today`?: string (null = por defecto)

Ejemplo: `{"variant":"recent","today":"2026-10-07","events":[{"id":"s1","kind":"status_update","at":"2026-10-07T16:00:00Z","subject":"Pipeline listo para pruebas","actor":"Luis Pérez"},{"id":"p1","kind":"page_published","at":"2026-10-06T18:00:00Z","subject":"Manual de uso","actor":"Pai"},{"id":"p2","kind":"page_published","at":"2026-10-06T17:30:00Z","subject":"Glosario","actor":"Pai"},{"id":"m1","kind":"milestone_completed","at":"2026-09-26","subject":"Descubrimiento"}]}`

#### OrganizationMembers

«Miembros» de los ajustes de una organización, como en el Portal: pestañas Miembros activos (nombre, correo y rol: owner, admin o member) e Invitaciones pendientes (correo, rol y vencimiento). Sólo lectura. Usa lo que devolvió organization_get.

- `members`: [{ name: string (min 1, ≤160), email?: string (≤200) (null = por defecto), role: "owner"|"admin"|"member" }] (máx 100)
- `invitations`?: [{ email: string (min 3, ≤200), role: "owner"|"admin"|"member", expiresAt: string }] (máx 50) (null = por defecto)

Ejemplo: `{"members":[{"name":"Marta Ruiz","email":"marta@clinica.mx","role":"owner"},{"name":"Luis Pérez","email":"luis@clinica.mx","role":"member"}],"invitations":[{"email":"ana@clinica.mx","role":"admin","expiresAt":"2026-10-14T18:00:00Z"}]}`

#### OrganizationsGrid

«Tus organizaciones», el inicio del Portal: una tarjeta por organización con sus iniciales, su nombre y sus miembros; active marca la organización activa y create agrega la tarjeta «Crear organización» (staff). En la vista «Abrir» no navega. Usa lo que devolvió organization_list.

- `organizations`: [{ name: string (min 1, ≤160), members: integer (≥0, ≤9007199254740991), active?: boolean (null = por defecto) }] (min 1, máx 40)
- `create`?: boolean (null = por defecto)

Ejemplo: `{"organizations":[{"name":"Clínica Santa Fe","members":7,"active":true},{"name":"Distribuidora del Norte","members":3}]}`

#### Payments

«Pagos» de un proyecto, la tabla de Portal y Console: lo que el cliente debe (facturas abiertas con su saldo, invoices; el siguiente hito sin factura, next) y lo pagado (payments), con búsqueda, filtros de estado y moneda, orden, páginas y la hoja de cada fila en la vista. Montos en unidades (no centavos); un pago con invoice dice su concepto («Hito: …», propuesta y factura). audience staff es la de Console (marcas internas y su texto vacío). 25 filas por página. Nunca muestra datos bancarios: las filas pendientes no se abren (la cuenta para pagar sólo la da Portal). Usa lo que devolvió payment_list.

- `payments`: [{ id: string (min 1, ≤80), paidAt: string, amount: number (≥0), currency: string (min 3, ≤3), method: "spei"|"transfer"|"card"|"cash"|"other", status?: "confirmed"|"void"|null (null = por defecto), reference?: string (min 1, ≤160) (null = por defecto), payer?: string (min 1, ≤160) (null = por defecto), invoice?: { folio?: string (≤40) (null = por defecto), milestone?: string (min 1, ≤160) (null = por defecto), proposal?: string (min 1, ≤160) (null = por defecto), description?: string (≤2000) (null = por defecto) } (null = por defecto) }] (máx 200)
- `invoices`?: [{ id: string (min 1, ≤80), folio?: string (≤40) (null = por defecto), issuedAt: string, total: number (≥0), balance: number (≥0), currency: string (min 3, ≤3), description?: string (≤2000) (null = por defecto), milestone?: string (min 1, ≤160) (null = por defecto), proposal?: string (min 1, ≤160) (null = por defecto) }] (máx 100) (null = por defecto)
- `next`?: [{ milestone: string (min 1, ≤160), sequence: integer (≥0, ≤9007199254740991), amount: number (≥0), currency: string (min 3, ≤3), due?: string (null = por defecto), proposal: string (min 1, ≤160) }] (máx 20) (null = por defecto)
- `audience`?: "client"|"staff"|null (null = por defecto)

Ejemplo: `{"payments":[{"id":"p1","paidAt":"2026-09-15T17:20:00Z","amount":46400,"currency":"MXN","method":"spei","reference":"ANTICIPO-H1"}],"invoices":[{"id":"f2","folio":"A-102","issuedAt":"2026-10-01T12:00:00Z","total":58000,"balance":58000,"currency":"MXN","milestone":"Construcción del CRM","proposal":"CRM comercial"}],"next":[{"milestone":"Lanzamiento","sequence":3,"amount":30000,"currency":"MXN","due":"2026-11-20T00:00:00Z","proposal":"CRM comercial"}]}`

#### ProductDetail

«Inicio» de un producto de Pai, como lo ve el cliente en Portal: estado, tipo, alojamiento, URL de producción, ambientes, dominios, enlaces (repositorio, monitoreo…) y proyectos ligados; pendingStatus muestra un cambio de estado por aprobar. Sólo lectura: nada se aprueba ni se cambia. Usa lo que devolvió product_get.

- `name`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `type`: "web"|"mobile"|"integration"|"api"|"website"|"other"
- `hosting`: "pai"|"external"
- `status`: "draft"|"building"|"testing"|"live"|"retired"
- `pendingStatus`?: "draft"|"building"|"testing"|"live"|"retired"|null (null = por defecto)
- `productionUrl`?: string (null = por defecto)
- `environments`?: [{ kind: "production"|"staging"|"development"|"preview", url?: string (null = por defecto), provider?: string (min 1, ≤160) (null = por defecto) }] (máx 10) (null = por defecto)
- `domains`?: [string (min 1, ≤253)] (máx 20) (null = por defecto)
- `links`?: [{ kind: "repository"|"dashboard"|"docs"|"monitoring"|"design"|"other", url: string, label?: string (min 1, ≤160) (null = por defecto) }] (máx 20) (null = por defecto)
- `projects`?: [{ name: string (min 1, ≤160), status: string (≤40) }] (máx 20) (null = por defecto)

Ejemplo: `{"name":"Shopi","description":"Tienda en línea de la marca.","type":"web","hosting":"pai","status":"testing","productionUrl":"https://app.shopi.mx","environments":[{"kind":"production","url":"https://app.shopi.mx","provider":"Railway"},{"kind":"staging","url":"https://staging.shopi.mx","provider":"Railway"}],"domains":["app.shopi.mx"],"projects":[{"name":"Sitio web","status":"active"}]}`

#### ProductsList

«Productos» de una organización, la lista de Portal y Console: nombre, clase (Pai App o externo), tipo, estado (con «Aprobación pendiente» si pendingStatus), URL de producción y última actualización, con búsqueda, filtros de estado y clase, orden y páginas en la vista. create dibuja «Nuevo producto» de Console (inerte) a la derecha de los filtros y en el estado vacío. Usa lo que devolvió product_list.

- `products`: [{ id: string (min 1, ≤80), name: string (min 1, ≤160), description?: string (≤2000) (null = por defecto), type: "web"|"mobile"|"integration"|"api"|"website"|"other", hosting: "pai"|"external", status: "draft"|"building"|"testing"|"live"|"retired", pendingStatus?: "draft"|"building"|"testing"|"live"|"retired"|null (null = por defecto), productionUrl?: string (null = por defecto), updatedAt: string }] (máx 200)
- `create`?: boolean (null = por defecto)

Ejemplo: `{"products":[{"id":"shopi","name":"Shopi","type":"web","hosting":"pai","status":"live","productionUrl":"https://app.shopi.mx","updatedAt":"2026-10-02T15:00:00Z"},{"id":"crm","name":"CRM comercial","type":"web","hosting":"pai","status":"testing","pendingStatus":"live","updatedAt":"2026-10-06T11:00:00Z"},{"id":"erp","name":"Integración con el ERP","type":"integration","hosting":"external","status":"building","updatedAt":"2026-09-21T09:00:00Z"}]}`

#### ProjectsTable

«Proyectos» de una organización, la lista del Portal: nombre, descripción, estado y fecha de creación, con búsqueda, filtro de estado, orden y páginas en la vista. Usa lo que devolvió project_list.

- `projects`: [{ id: string (min 1, ≤80), name: string (min 1, ≤160), description?: string (≤2000) (null = por defecto), status: "draft"|"planned"|"active"|"on_hold"|"completed"|"cancelled", createdAt: string }] (máx 200)

Ejemplo: `{"projects":[{"id":"web","name":"Sitio web","description":"Rediseño y CMS.","status":"active","createdAt":"2026-09-01T10:00:00Z"},{"id":"crm","name":"CRM comercial","status":"planned","createdAt":"2026-09-20T10:00:00Z"}]}`

#### ProposalLifecycle

Ciclo contractual de una propuesta (la pestaña «Ciclo de vida» de Portal): creada, enviada, aceptada (por quién) o rechazada (con su motivo), cada una con su fecha. No son versiones del documento; para eso usa HistoryPanel.

- `createdAt`: string
- `sentAt`?: string (null = por defecto)
- `acceptedAt`?: string (null = por defecto)
- `acceptedBy`?: string (min 1, ≤160) (null = por defecto)
- `rejectedAt`?: string (null = por defecto)
- `rejectionReason`?: string (≤2000) (null = por defecto)

Ejemplo: `{"createdAt":"2026-09-27T09:30:00Z","sentAt":"2026-09-30T16:00:00Z","acceptedAt":"2026-10-02T18:10:00Z","acceptedBy":"Marta Ruiz"}`

#### ProposalSummary (admite hijos)

Resumen comercial de una propuesta, como arriba del documento en Portal y Console: estado, inversión (amount en unidades, «+ IVA»), plazo de respuesta con «Vence en N días» y, si ya se decidió, quién y cuándo aceptó o el motivo del rechazo. title la encabeza con su badge de estado. Sus hijos van al pie (el siguiente paso).

- `title`?: string (min 1, ≤160) (null = por defecto)
- `status`: "draft"|"sent"|"accepted"|"rejected"|"expired"
- `amount`?: number (≥0) (null = por defecto)
- `currency`?: string (min 3, ≤3) (null = por defecto)
- `expiresAt`?: string (null = por defecto)
- `acceptanceWindowDays`?: integer (≥1, ≤365) (null = por defecto)
- `acceptedAt`?: string (null = por defecto)
- `acceptedBy`?: string (min 1, ≤160) (null = por defecto)
- `rejectedAt`?: string (null = por defecto)
- `rejectionReason`?: string (≤2000) (null = por defecto)
- `now`?: string (null = por defecto)

Ejemplo: `{"title":"Construcción del CRM","status":"sent","amount":11000,"currency":"USD","expiresAt":"2026-10-10T23:59:00Z","now":"2026-10-07T12:00:00Z"}`

#### Resources

Una carpeta de Recursos como la muestra el Portal: sus subcarpetas (con cuántas páginas y archivos tienen y sus primeras entradas) y sus páginas y archivos (tipo, tamaño y fecha), en tarjetas (layout grid, por omisión) o filas (list). Usa lo que devolvió page_list o file_list. No enlaza ni abre nada.

- `folders`?: [{ name: string (min 1, ≤160), pages: integer (≥0, ≤9007199254740991), files: integer (≥0, ≤9007199254740991), updatedAt?: string (null = por defecto), preview?: [string (min 1, ≤160)] (máx 3) (null = por defecto) }] (máx 40) (null = por defecto)
- `entries`?: [{ title: string (min 1, ≤160), kind: "page"|"file", mimeType?: string (≤100) (null = por defecto), sizeBytes?: integer (≥0, ≤9007199254740991) (null = por defecto), updatedAt?: string (null = por defecto) }] (máx 100) (null = por defecto)
- `layout`?: "grid"|"list"|null (null = por defecto)

Ejemplo: `{"folders":[{"name":"Entregables","pages":2,"files":1,"updatedAt":"2026-10-02T15:00:00Z","preview":["Alcance","Plan de pruebas"]}],"entries":[{"title":"Brief del proyecto","kind":"page","updatedAt":"2026-09-20T12:00:00Z"},{"title":"Contrato firmado.pdf","kind":"file","mimeType":"application/pdf","sizeBytes":482113,"updatedAt":"2026-09-25T18:00:00Z"}]}`

### Grupo: Conocimiento

#### C4Diagram

Diagrama C4 de Conocimiento, el mismo de Portal, en uno de sus cuatro niveles (context, container, component, code): elementos dentro del límite, personas y sistemas externos, relaciones con qué hacen y su tecnología (agrupadas y enrutadas para no encimarse). view es exactamente la proyección `c4` que devuelve la tool knowledge_view (no la escribas a mano). Con href, cada elemento y los botones de nivel llevan a la página del nodo ({id}, más ?level=); sin href no hay enlaces.

- `view`: objeto que viene de `knowledge_view` tal cual (no lo escribas a mano)
- `href`?: string (≤500) (null = por defecto)
- `height`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"view":"‹resultado de knowledge_view›","height":"md"}`

#### ErdDiagram

Diagrama entidad-relación de Conocimiento, el mismo de Portal: tablas con sus columnas (PK/FK/UQ), relaciones con cardinalidad pata de gallo y, en un ERD de sistema, un marco por modelo. view es exactamente la proyección `erd` que devuelve la tool knowledge_view (no la escribas a mano). href lleva a la página de cada tabla o modelo ({id}); sin href no hay enlaces. focus resalta una tabla.

- `view`: objeto que viene de `knowledge_view` tal cual (no lo escribas a mano)
- `href`?: string (≤500) (null = por defecto)
- `focus`?: string (≤200) (null = por defecto)
- `height`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"view":"‹resultado de knowledge_view›","focus":"venta","height":"md"}`

#### KnowledgeGraph

Grafo de Conocimiento, el mismo de Portal (WebGL): un punto por nodo, coloreado por su kind, y una línea por relación. Se arrastra, se acerca y al elegir un punto se resaltan sus vecinos y su título. Con href, el nodo elegido enlaza a su página ({id}). Usa los nodos y relaciones que devolvieron knowledge_list, knowledge_get o knowledge_context.

- `nodes`: [{ id: string (min 1, ≤200), title: string (min 1, ≤200), kind: "objective"|"decision"|"adr"|"business_rule"|"constraint"|"risk"|"question"|"assumption"|"task"|"pattern"|"runbook"|"gotcha"|"antipattern"|"note"|"concept"|"fact"|"reference"|"module"|"screen"|"flow"|"data_model"|"entity"|"component"|"actor"|"glossary_term" }] (min 1, máx 500)
- `edges`: [{ source: string (min 1, ≤200), target: string (min 1, ≤200), rel: string (min 1, ≤40) }] (máx 1500)
- `href`?: string (≤500) (null = por defecto)
- `height`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"nodes":[{"id":"dec-stack","title":"API monolítica en NestJS","kind":"decision"},{"id":"mod-ventas","title":"Ventas / Expediente","kind":"module"},{"id":"mod-clientes","title":"Clientes","kind":"module"},{"id":"act-asesor","title":"Asesor de ventas","kind":"actor"},{"id":"q-crm","title":"¿El CRM entra en F1?","kind":"question"}],"edges":[{"source":"dec-stack","target":"mod-ventas","rel":"affects"},{"source":"dec-stack","target":"mod-clientes","rel":"affects"},{"source":"act-asesor","target":"mod-ventas","rel":"performs"},{"source":"q-crm","target":"mod-clientes","rel":"refers_to"}],"height":"sm"}`

#### KnowledgeKindBadge

El tipo de un nodo de Conocimiento como lo pinta Pai: badge con su punto de color y su nombre («• Componente (C4)»).

- `kind`: "objective"|"decision"|"adr"|"business_rule"|"constraint"|"risk"|"question"|"assumption"|"task"|"pattern"|"runbook"|"gotcha"|"antipattern"|"note"|"concept"|"fact"|"reference"|"module"|"screen"|"flow"|"data_model"|"entity"|"component"|"actor"|"glossary_term"

Ejemplo: `{"kind":"decision"}`

#### KnowledgeTable

La biblioteca de Conocimiento de Portal y Console: tabla de nodos con tipo, estado, proyecto (project; sin él, «Organización»), visibilidad y fecha, con búsqueda, filtros, orden y páginas dentro de la vista. showProject:false es la biblioteca de un proyecto: sin columna de proyecto, y sólo los nodos con organization:true llevan «Organización» bajo el título. Con href (plantilla con {id}) el título enlaza a la página del nodo. Usa los nodos que devolvió knowledge_search o knowledge_list.

- `items`: [{ id: string (min 1, ≤80), title: string (min 1, ≤200), kind: "objective"|"decision"|"adr"|"business_rule"|"constraint"|"risk"|"question"|"assumption"|"task"|"pattern"|"runbook"|"gotcha"|"antipattern"|"note"|"concept"|"fact"|"reference"|"module"|"screen"|"flow"|"data_model"|"entity"|"component"|"actor"|"glossary_term", status: "draft"|"proposed"|"active"|"resolved"|"superseded"|"archived"|"rejected", visibility?: "internal"|"client"|null (null = por defecto), summary?: string (≤400) (null = por defecto), project?: string (min 1, ≤160) (null = por defecto), organization?: boolean (null = por defecto), updatedAt: string }] (máx 200)
- `showProject`?: boolean (null = por defecto)
- `href`?: string (≤500) (null = por defecto)
- `search`?: string (≤120) (null = por defecto)

Ejemplo: `{"items":[{"id":"dec-stack","title":"API monolítica en NestJS","kind":"decision","status":"active","visibility":"client","project":"Sitio web","updatedAt":"2026-10-02T15:00:00Z"},{"id":"rule-iva","title":"Los precios se muestran sin IVA","kind":"business_rule","status":"active","visibility":"client","updatedAt":"2026-09-20T10:00:00Z"},{"id":"q-crm","title":"¿El CRM entra en F1?","kind":"question","status":"proposed","visibility":"internal","project":"CRM","updatedAt":"2026-10-05T18:30:00Z"}]}`

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
