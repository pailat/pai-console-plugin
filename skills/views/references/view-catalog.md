# Catálogo de vistas `pai-view@1`

> Generado por `tools/gen-references.ts` desde pai-portal `dfc02d78` (2026-10-11 merge: mcp-pages @45e2e4f0 (#169: page_update con título y descripción, page_move reescribe URLs absolutas del Portal, escrituras y page_list compactos, filtros de DataTable por celda)), `packages/views/src/catalog.ts`. No editar a mano: regenerar.

Formato: Spec plano de json-render: { root: id, elements: { [id]: { type, props, children? } } }. Los hijos se referencian por id.

## Reglas

- Usa sólo los componentes de este catálogo; no hay className, style, colores ni HTML.
- Cada objeto de props es cerrado: sólo las props de su esquema; las demás se rechazan.
- Los ids son únicos, empiezan con letra y se reutilizan al editar.
- Las props omitidas que aceptan null toman su valor por defecto.
- Sólo AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell, ContactSection, AuthLayout, BoardLayout, ChatLayout, DashboardLayout, DetailLayout, DocLayout, EmptyLayout, FilesLayout, FormLayout, PageLayout, SettingsLayout, SplitView, WizardLayout, Card, Collapsible, DetailSheet, DialogFrame, Frame, Grid, Section, Stack, Tabs, UnderlinedTabs, Tooltip, ButtonGroup, Popover, Stepper y ProposalSummary tienen hijos; Tabs y UnderlinedTabs llevan un hijo por pestaña, en orden.
- Elige el layout con la raíz de la vista: AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell son pantallas completas (ver layouts) y van sólo en la raíz; un documento, reporte o tablero empieza con Stack. Nunca recrees una pantalla de Pai con AppShell: AppShell es para apps de clientes.
- Antes de usar un componente, pide su descripción, su esquema y su ejemplo con view_catalog({ types: [...] }) o por grupo (view_catalog({ group })); aquí sólo están su resumen y, en los grupos con index props, sus props por nombre (nombre? es opcional). Los grupos con index names sólo traen el resumen: pide sus props por grupo.
- Un patrón (grupo patterns) lleva un hijo por región, en el orden de sus regiones; regions elige cuáles usa, en ese mismo orden.
- Para una pantalla completa puedes partir de una receta (recipes): pídela con view_catalog({ recipe }) y cambia sus datos por los tuyos. Es opcional.
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

- **AppShell**: App de un cliente: barra lateral con menú y usuario, encabezado y contenido. Sólo raíz.
- **AuthFrame**: Pantalla de identidad de Pai (login, registro, invitación) con su tarjeta. Sólo raíz.
- **ConsoleShell**: Pantalla de Console idéntica a la real: menú, migas y título. Sólo raíz.
- **PortalShell**: Pantalla del Portal idéntica a la real: selector de org, menú del área y migas. Sólo raíz.
- **SiteShell**: Página de pai.lat con su header, footer y cookies; hijos: secciones del sitio. Sólo raíz.
- **Stack**: Documento, reporte o tablero dentro de una página de Recursos (sin chrome de app).

## Grupos

| Grupo | Para | Componentes |
|---|---|---|
| Aplicación | Pantallas completas, sólo en la raíz: las apps de Pai, pai.lat, login y la app de un cliente. | AppShell, AuthFrame, ConsoleShell, PortalShell, SiteShell |
| Sitio web | Secciones de un sitio web (pai.lat o el de un cliente) dentro de SiteShell. | BlogList, ContactSection, CtaBand, HowItWorks, LogoGrid, SectionIntro, ServiceCards, SiteHero, Testimonials |
| Patrones | Layouts de pantalla con regiones con nombre (encabezado, principal, lateral…): un hijo por región, en orden. Van dentro de un shell o en la raíz. | AuthLayout, BoardLayout, ChatLayout, DashboardLayout, DetailLayout, DocLayout, EmptyLayout, FilesLayout, FormLayout, PageLayout, SettingsLayout, SplitView, WizardLayout |
| Estructura | Contenedores que ordenan la vista. | Accordion, Card, Collapsible, DetailSheet, DialogFrame, Frame, Grid, Section, Separator, Stack, Tabs, UnderlinedTabs |
| Contenido | Títulos, texto, etiquetas, avisos, listas, enlaces y código. | Alert, Avatar, Badge, CodeBlock, CommentsPanel, Heading, HistoryPanel, HoverCard, IconTile, Item, Kbd, Link, List, Rating, StatusBadge, StatusDot, Text, Tooltip |
| Datos | Indicadores, tablas, gráficas y pares etiqueta–valor. | BarList, Chart, DataTable, FileList, Heatmap, KeyValue, Metric, Progress, ProgressRing, Stats, Table, Tree, TreeTable |
| Controles | Botones, menús y campos de formulario. Responden dentro de la vista (abren, cambian, se marcan) pero nada se envía, guarda ni navega, salvo un botón con href. | ActionMenu, Autocomplete, Button, ButtonGroup, Calendar, Checkbox, Command, DateSelector, Dropzone, FilterBar, Input, Popover, RadioGroup, Select, Switch, Textarea, ToggleGroup |
| Formularios | Campos de formulario de maqueta: se ven como en Pai pero no se enfocan, no envían ni guardan nada, ni piden datos sensibles. | Cascader, Combobox, InputOTP, NumberField, PhoneInput, SignaturePad, Slider, TimePicker |
| Conversación | Maquetas de un chat con un agente: mensajes y el cuadro para escribir. No se conectan a ningún agente ni envían mensajes. | ChatComposer, ChatThread |
| Navegación | Migas, paginación y piezas sueltas del chrome de Pai. | Breadcrumb, Menubar, NavigationMenu, OrgSwitcher, PageBar, PageHeader, Pagination, ProjectHeader, ProjectSwitcher |
| Estados | Vacío, error y carga de una sección, con el aspecto que usan Portal y Console. | EmptyState, ErrorState, LoadingState, Skeleton, Spinner |
| Planeación | Cronologías, etapas, pasos, hitos, Tareas y Kanban. | Checklist, EventCalendar, Gantt, Kanban, MilestoneGanttLegend, MilestoneGanttSkeleton, MilestoneTimeline, Stages, Stepper, TaskBoard, Timeline |
| Proyecto | Piezas de las pantallas de un proyecto en Portal y Console: propuestas, pagos, productos. Sólo muestran lo que la vista trae; nada se guarda. | ActivityFeed, OrganizationMembers, OrganizationsGrid, Payments, ProductDetail, ProductsList, ProjectsTable, ProposalLifecycle, ProposalSummary, Resources |
| Comercio | Planes, comparativas y reseñas del cliente, sólo informativos: nada se compra, cobra ni envía, y los precios son del cliente, no de Pai. | ComparisonTable, PricingGrid, ReviewList |
| Conocimiento | Diagramas del grafo (ERD, C4, nodos), la biblioteca y el badge de tipo. Los diagramas se mueven y acercan en la vista. | C4Diagram, ErdDiagram, KnowledgeGraph, KnowledgeKindBadge, KnowledgeTable |

## Componentes

Cada objeto de props es cerrado. `?` marca una prop opcional; las que aceptan `null` toman su valor por defecto si se omiten. Las props «que vienen de» una tool se copian tal cual de su respuesta.

### Grupo: Aplicación

#### AppShell (admite hijos)

App completa de un cliente, sólo raíz: marca, menú con iconos y badge opcional, usuario y contenido. layout sidebar (null) conserva la barra lateral; inset usa el lateral con contenido en SidebarInset; topbar muestra marca, menú horizontal y usuario (no admite secondaryNav: se ignora). En una página, la barra lateral se pliega a iconos con tooltip si la vista no es ancha, y en angosto el menú abre con un botón. breadcrumb muestra migas antes de title; sus href navegan. En Recursos se ve en un marco de dispositivos y puede abrirse a pantalla completa.

- `brand`: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) }
- `nav`: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap", active?: boolean (null = por defecto), badge?: string (min 1, ≤6) (null = por defecto) }] (min 1, máx 12)
- `secondaryTitle`?: string (≤80) (null = por defecto)
- `secondaryNav`?: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap", active?: boolean (null = por defecto), badge?: string (min 1, ≤6) (null = por defecto) }] (máx 12) (null = por defecto)
- `layout`?: "sidebar"|"inset"|"topbar"|null (null = por defecto)
- `breadcrumb`?: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 4) (null = por defecto)
- `title`: string (min 1, ≤160)
- `user`?: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) } (null = por defecto)

Ejemplo: `{"brand":{"name":"Portenta","detail":"Ciclo de venta"},"nav":[{"label":"Dashboard","icon":"dashboard","active":true},{"label":"Ventas","icon":"file"},{"label":"Clientes","icon":"users"}],"title":"Dashboard comercial","user":{"name":"Julio César Vega","detail":"Dirección Comercial"}}`

#### AuthFrame (admite hijos)

Pantalla de identidad de Pai (iniciar sesión, registro, invitación), idéntica a la real: fondo animado de Pai, logo blanco y una tarjeta centrada con title y description; sus hijos van dentro de la tarjeta (Input, Button, Text, Separator…). Va siempre como raíz de la vista. Es una maqueta: los campos y botones se pintan deshabilitados, nada se escribe ni se envía.

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

Pantalla del Portal de Pai, idéntica a la real: selector de organización, el menú real del área (home, organization, project o product) tal como lo ve un cliente o el staff de Pai (audience), usuario al pie y la barra con migas. Sus hijos son el contenido de la página. Va siempre como raíz de la vista. active es la clave del ítem activo del menú (projects, milestones, payments…). menu reemplaza el menú real sólo para pantallas que Portal aún no tiene. Nada navega.

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

#### BlogList

Lista de artículos de un sitio (pai.lat o el de un cliente) en tarjetas: title, excerpt, date opcional (AAAA-MM-DD), category opcional y href opcional (ruta del Portal o https; sin él, la tarjeta no enlaza). title opcional encabeza la sección. Usa sólo artículos que existan: no inventes títulos ni enlaces.

- `title`?: string (min 1, ≤200) (null = por defecto)
- `posts`: [{ title: string (min 1, ≤160), excerpt: string (≤2000), date?: string (null = por defecto), category?: string (min 1, ≤160) (null = por defecto), href?: string (null = por defecto) }] (min 1, máx 9)

Ejemplo: `{"title":"Del blog","posts":[{"title":"Cinco formas de reducir las citas perdidas","excerpt":"Recordatorios, confirmación en un clic y lista de espera: lo que nos funcionó en tres sucursales.","date":"2026-09-18","category":"Operación","href":"https://pai.lat/blog"},{"title":"Cómo elegir horarios que sí se llenan","excerpt":"Lo que aprendimos de un año de agenda en línea en clínicas dentales.","date":"2026-08-30","category":"Agenda"}]}`

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

#### HowItWorks

Sección «cómo funciona» de un sitio (pai.lat o el de un cliente): de 2 a 6 pasos numerados en orden, cada uno con title y body; en pantallas anchas van en fila (hasta 3 por fila), en angostas uno bajo otro. title y intro opcionales encabezan la sección. Para tarjetas de servicios usa ServiceCards.

- `title`?: string (min 1, ≤200) (null = por defecto)
- `intro`?: string (≤2000) (null = por defecto)
- `steps`: [{ title: string (min 1, ≤160), body: string (≤2000) }] (min 2, máx 6)

Ejemplo: `{"title":"Cómo agendar tu cita","steps":[{"title":"Elige la sucursal","body":"Ve las sucursales cercanas y sus horarios."},{"title":"Escoge el horario","body":"Sólo aparecen los horarios libres de ese día."},{"title":"Recibe la confirmación","body":"Te llega por correo, con un recordatorio un día antes."}]}`

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

Hero de un sitio. variant pai (o null) es el de la home de pai.lat, el real: fondo de puntos y malla de color animada, sello opcional (badge, p. ej. «Stripe Premier Partner»), titular grande cuyo final (highlight) va en el color de marca, introducción y dos llamadas (primary sólida, secondary discreta). variant plain es el de un sitio de cliente: el mismo titular, intro y llamadas, sin el degradado ni la malla de Pai (highlight sigue al titular, sin color). Primer hijo de SiteShell.

- `badge`?: string (min 1, ≤160) (null = por defecto)
- `title`: string (min 1, ≤200)
- `highlight`?: string (≤120) (null = por defecto)
- `intro`: string (≤2000)
- `primary`?: string (min 1, ≤160) (null = por defecto)
- `secondary`?: string (min 1, ≤160) (null = por defecto)
- `variant`?: "pai"|"plain"|null (null = por defecto)

Ejemplo: `{"badge":"Stripe Premier Partner","title":"Hacemos simple lo complejo, ","highlight":"posible lo imposible.","intro":"Diseñamos, construimos y operamos productos digitales, pagos e IA para empresas y plataformas en México y Latinoamérica.","primary":"Hablemos de tu proyecto","secondary":"Explora cómo trabajamos"}`

#### Testimonials

Sección de testimonios de un sitio (pai.lat o el de un cliente): de 1 a 6 citas con quote, author, role opcional (cargo y empresa) y source. Usa sólo citas y calificaciones que vengan de datos del cliente o de una herramienta: no inventes testimonios, nombres ni estrellas. source dice de dónde salen (p. ej. «Encuesta NPS sep 2026», «Google Reviews»); sin source, el item se marca «Ejemplo» y no se presenta como real. title opcional encabeza la sección.

- `title`?: string (min 1, ≤200) (null = por defecto)
- `items`: [{ quote: string (≤2000), author: string (min 1, ≤160), role?: string (min 1, ≤160) (null = por defecto), source?: string (min 2, ≤60) (null = por defecto) }] (min 1, máx 6)

Ejemplo: `{"title":"Lo que dicen nuestros pacientes","items":[{"quote":"Agendar mi cita me tomó un minuto y me llegó el recordatorio un día antes.","author":"Mariana López","role":"Paciente desde 2024","source":"Google Reviews"},{"quote":"Dejamos de perder citas por olvidos: los recordatorios hicieron la diferencia.","author":"Dra. Paula Méndez","role":"Directora, sucursal Roma","source":"Encuesta NPS sep 2026"}]}`

### Grupo: Patrones

#### AuthLayout (admite hijos)

Pantalla de acceso o registro de la app de un cliente, sólo como maqueta: brand (Heading o Text con el nombre de la app), form (Input de correo, Checkbox, Button) y aside (un panel con texto o una cita). Un hijo por región, en ese orden; regions elige cuáles usa. El formulario se pinta deshabilitado: se lee, pero nada se enfoca ni se envía. asideSide end (por omisión) o start; en pantallas angostas el panel se oculta. Dentro sólo admite los del grupo forms y Stack, Grid, Section, Frame, Separator, Heading, Text, Alert, Badge, StatusBadge, StatusDot, Avatar, IconTile, Kbd, List, Link, Item, EmptyState, ErrorState, LoadingState, Skeleton, Spinner, Button, ButtonGroup, Checkbox, Input, RadioGroup, Select, Switch, Textarea, DateSelector, Autocomplete y Stages. Para las pantallas de identidad de Pai usa AuthFrame. Nunca pidas contraseñas reales ni códigos: usa sólo campos de ejemplo.

- `regions`?: ["brand"|"form"|"aside"] (min 1, máx 3) (null = por defecto)
- `asideSide`?: "start"|"end"|null (null = por defecto)

Ejemplo: `{"asideSide":"end"}`

#### BoardLayout (admite hijos)

Pantalla de tablero o agenda: toolbar (FilterBar, ToggleGroup, Button), board (Kanban, Gantt, TaskBoard o EventCalendar; se desplaza en horizontal si no cabe) y aside (KeyValue, Item, ActivityFeed). Un hijo por región, en ese orden; regions elige cuáles usa. aside va a la derecha en pantallas anchas (asideWidth narrow 18rem o medium 22rem, por omisión) y debajo en angostas.

- `regions`?: ["toolbar"|"board"|"aside"] (min 1, máx 3) (null = por defecto)
- `asideWidth`?: "narrow"|"medium"|null (null = por defecto)

Ejemplo: `{"asideWidth":"medium"}`

#### ChatLayout (admite hijos)

Pantalla de una conversación con un agente, de maqueta: no se conecta a ningún agente ni envía mensajes. thread lleva el hilo (ChatThread), composer el cuadro para escribir (ChatComposer, que ya es maqueta por sí mismo) y aside un lateral opcional (contexto, archivos, pasos: KeyValue, List, FileList…). Un hijo por región, en ese orden; regions elige cuáles usa. En pantallas anchas aside va a la derecha; en angostas, debajo. Dentro de Card no dibuja un marco propio.

- `regions`?: ["thread"|"composer"|"aside"] (min 1, máx 3) (null = por defecto)

Ejemplo: `{}`

#### DashboardLayout (admite hijos)

Tablero dentro de un shell (PortalShell, AppShell) o en la raíz. kpis contiene Stats; main, Chart o DataTable; side, BarList, Timeline o Item; footer, DataTable. regions elige las regiones presentes y sus hijos las llenan en ese orden, uno por región. side define el ancho del lateral: narrow (1/3, por omisión) o wide (1/2). Cada región trae su marco.

- `regions`?: ["kpis"|"main"|"side"|"footer"] (min 1, máx 4) (null = por defecto)
- `side`?: "narrow"|"wide"|null (null = por defecto)

Ejemplo: `{"side":"narrow"}`

#### DetailLayout (admite hijos)

Detalle dentro de un shell o en la raíz: header (PageHeader, ProjectHeader o Heading), summary (KeyValue o Stats), main (Tabs, Section, Timeline o DataTable), aside (KeyValue, Item, ActivityFeed o Checklist). regions elige las regiones y sus hijos las llenan en ese orden, uno por región. asideSide coloca el lateral al inicio o al final en pantallas anchas; en angostas queda al final. stickyAside fija el lateral al hacer scroll.

- `regions`?: ["header"|"summary"|"main"|"aside"] (min 1, máx 4) (null = por defecto)
- `asideSide`?: "end"|"start"|null (null = por defecto)
- `stickyAside`?: boolean (null = por defecto)

Ejemplo: `{"asideSide":"end","stickyAside":true}`

#### DocLayout (admite hijos)

Layout de un documento largo (manual, política, especificación): header (PageHeader o Heading), toc (el índice: un List o un Stack de Item con los títulos de las secciones) y content (Section tras Section). Un hijo por región, en ese orden; regions elige cuáles usa. En pantallas anchas el índice va a la izquierda y se queda fijo al hacer scroll (tocWidth narrow 12rem o medium 16rem, por omisión); en angostas va arriba.

- `regions`?: ["header"|"toc"|"content"] (min 1, máx 3) (null = por defecto)
- `tocWidth`?: "narrow"|"medium"|null (null = por defecto)

Ejemplo: `{"tocWidth":"medium"}`

#### EmptyLayout (admite hijos)

Estado vacío de una pantalla o sección más rico que EmptyState: visual (IconTile o un Skeleton de lo que vendrá), message (Heading y Text), actions (Button o ButtonGroup) y preview (una muestra de cómo se verá: Card, Table o Chart de ejemplo). Un hijo por región, en ese orden; regions elige cuáles usa. layout centered (por omisión) centra todo y pone preview debajo; split pone el mensaje a la izquierda y preview a la derecha en pantallas anchas. Para un vacío simple usa EmptyState.

- `regions`?: ["visual"|"message"|"actions"|"preview"] (min 1, máx 4) (null = por defecto)
- `layout`?: "centered"|"split"|null (null = por defecto)

Ejemplo: `{"layout":"centered"}`

#### FilesLayout (admite hijos)

Explorador de archivos o documentos: tree (Tree de carpetas), list (FileList o DataTable de archivos) y preview (el detalle del archivo elegido: KeyValue, Text, Card). Un hijo por región, en ese orden; regions elige cuáles usa. En pantallas anchas van en tres columnas (árbol de treeWidth narrow 14rem o medium 18rem, por omisión; vista previa de 20rem); en angostas, una debajo de otra. Elegir en el árbol o la lista no cambia la vista: es estática.

- `regions`?: ["tree"|"list"|"preview"] (min 1, máx 3) (null = por defecto)
- `treeWidth`?: "narrow"|"medium"|null (null = por defecto)

Ejemplo: `{"treeWidth":"medium"}`

#### FormLayout (admite hijos)

Formulario de maqueta (alta, edición, contacto): intro (Heading y Text), fields (Input, Select, Textarea, Checkbox o los del grupo forms, en un Stack o Grid) y actions (Button o ButtonGroup). Un hijo por región, en ese orden; regions elige cuáles usa. Los campos y las acciones se pintan deshabilitados: se ven y se leen, pero no se enfocan, no se envían ni guardan nada. columns 2 pone los campos en dos columnas en pantallas anchas. Dentro sólo admite los del grupo forms y Stack, Grid, Section, Frame, Separator, Heading, Text, Alert, Badge, StatusBadge, StatusDot, Avatar, IconTile, Kbd, List, Link, Item, EmptyState, ErrorState, LoadingState, Skeleton, Spinner, Button, ButtonGroup, Checkbox, Input, RadioGroup, Select, Switch, Textarea, DateSelector, Autocomplete y Stages. Nunca pidas contraseñas, tarjetas, cuentas bancarias ni códigos de verificación.

- `regions`?: ["intro"|"fields"|"actions"] (min 1, máx 3) (null = por defecto)
- `columns`?: number | number (null = por defecto)

Ejemplo: `{"columns":1}`

#### PageLayout (admite hijos)

Layout de una página de producto, como las secciones de un proyecto en Portal: header (PageHeader o ProjectHeader), toolbar (FilterBar, ToggleGroup y botones), main (DataTable, TreeTable, Kanban, Stack…) y aside (KeyValue, Item, Timeline). Un hijo por región, en ese orden; regions elige cuáles usa (p. ej. ["header", "main"]). aside va a la derecha en pantallas anchas y debajo en angostas. width contained centra el contenido con un ancho de lectura (formularios, documentos); full (por omisión) usa todo el ancho. Va dentro de un shell (PortalShell, ConsoleShell, AppShell) o en la raíz.

- `regions`?: ["header"|"toolbar"|"main"|"aside"] (min 1, máx 4) (null = por defecto)
- `width`?: "full"|"contained"|null (null = por defecto)

Ejemplo: `{"width":"full"}`

#### SettingsLayout (admite hijos)

Pantalla de ajustes (de una cuenta, un espacio o un producto): nav es el menú de secciones (normalmente un Stack de Item o ToggleGroup vertical) y main el panel de la sección (Section con Input, Switch, Select…). Un hijo por región, en ese orden; regions elige cuáles usa. nav va a la izquierda y fijo al hacer scroll en pantallas anchas, y arriba en angostas. navWidth: narrow (12rem) o medium (16rem, por omisión). Elegir en nav no cambia main: la vista es estática.

- `regions`?: ["nav"|"main"] (min 1, máx 2) (null = por defecto)
- `navWidth`?: "narrow"|"medium"|null (null = por defecto)

Ejemplo: `{"navWidth":"medium"}`

#### SplitView (admite hijos)

Vista de lista y lectura: list contiene la lista de registros; detail muestra el registro elegido. regions elige cuáles usa y sus hijos las llenan en ese orden, uno por región. listWidth fija el ancho de la lista en pantallas anchas: narrow (18rem), medium (24rem, por omisión) o wide (32rem); en angostas se apilan. Elegir en la lista no cambia el detalle: la vista es estática. Dentro de Card no dibuja un marco propio.

- `regions`?: ["list"|"detail"] (min 1, máx 2) (null = por defecto)
- `listWidth`?: "narrow"|"medium"|"wide"|null (null = por defecto)

Ejemplo: `{"listWidth":"medium"}`

#### WizardLayout (admite hijos)

Asistente o alta guiada (onboarding, configuración): steps (Stages con el paso actual), main (el contenido del paso: campos, texto, opciones) y actions (Anterior, Siguiente). Un hijo por región, en ese orden; regions elige cuáles usa. orientation top (por omisión) pone los pasos arriba; side, a la izquierda en pantallas anchas. Todo se pinta deshabilitado (los pasos también): se ve y se lee, pero nada se enfoca, avanza ni envía. Dentro sólo admite los del grupo forms y Stack, Grid, Section, Frame, Separator, Heading, Text, Alert, Badge, StatusBadge, StatusDot, Avatar, IconTile, Kbd, List, Link, Item, EmptyState, ErrorState, LoadingState, Skeleton, Spinner, Button, ButtonGroup, Checkbox, Input, RadioGroup, Select, Switch, Textarea, DateSelector, Autocomplete y Stages.

- `regions`?: ["steps"|"main"|"actions"] (min 1, máx 3) (null = por defecto)
- `orientation`?: "top"|"side"|null (null = por defecto)

Ejemplo: `{"orientation":"top"}`

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

Detalle de un elemento (un pago, una tarea, un hito) con la anatomía del panel lateral de Pai: antetítulo, título, estados, descripción, cuerpo (sus hijos: KeyValue, Text, Timeline…; cada Section hija es una sección con rótulo) y acciones al pie. variant: detail (por omisión, un registro), create (alta) o settings (edición). presentation inline (por omisión) lo dibuja en la vista; overlay lo abre sobre la página con un botón (triggerLabel). Cerrar sólo lo oculta en la vista.

- `eyebrow`?: string (min 1, ≤160) (null = por defecto)
- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `badges`?: [{ label: string (min 1, ≤160), tone: "neutral"|"info"|"progress"|"success"|"warning"|"danger" }] (máx 4) (null = por defecto)
- `actions`?: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) }] (máx 3) (null = por defecto)
- `presentation`?: "inline"|"overlay"|null (null = por defecto)
- `open`?: boolean (null = por defecto)
- `triggerLabel`?: string (min 1, ≤160) (null = por defecto)
- `size`?: "md"|"lg"|null (null = por defecto)
- `variant`?: "detail"|"create"|"settings"|null (null = por defecto)

Ejemplo: `{"eyebrow":"Pago · 2 de 3","title":"Anticipo de construcción","description":"USD 4,000.00 · Transferencia","badges":[{"label":"Pagado","tone":"success"}],"actions":[{"label":"Descargar factura","icon":"download"}]}`

#### DialogFrame (admite hijos)

La maqueta de un diálogo o una confirmación, dibujada en su lugar de la vista: no se abre encima de la página, no oscurece el fondo ni atrapa el foco. title, description, icon opcional, tone destructive para una confirmación de borrar, y sus hijos son el cuerpo (Text, KeyValue, campos de maqueta…). actions son hasta 3 botones decorativos al pie (el primero, el principal); no navegan ni hacen nada. size: sm, md (por omisión) o lg.

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `tone`?: "default"|"destructive"|null (null = por defecto)
- `actions`?: [{ label: string (min 1, ≤160) }] (min 1, máx 3) (null = por defecto)
- `size`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"title":"¿Archivar el proyecto?","description":"El equipo dejará de verlo en la lista de proyectos activos.","tone":"destructive","actions":[{"label":"Archivar"},{"label":"Cancelar"}]}`

#### Frame (admite hijos)

Marco de paneles: un panel por hijo; stacked los une (ficha por secciones). Un solo bloque: Card.

- `title`?: string (min 1, ≤160) (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)
- `stacked`?: boolean (null = por defecto)
- `action`?: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) } (null = por defecto)

Ejemplo: `{"title":"Producto","description":"Ambientes y dominios.","stacked":true}`

#### Grid (admite hijos)

Cuadrícula de 1 a 6 columnas que se apila en pantallas angostas. Úsala para tarjetas de métricas (5 o 6 en una fila de KPIs) o grupos paralelos. Dentro de una AppShell en una página, 4 columnas caben antes.

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

Etiqueta corta de estado o categoría. tone (neutral, info, progress, success, warning, danger) la colorea y manda sobre variant.

- `text`: string
- `variant`?: "default"|"secondary"|"destructive"|"outline"|null (null = por defecto)
- `tone`?: "neutral"|"info"|"progress"|"success"|"warning"|"danger"|null (null = por defecto)

Ejemplo: `{"text":"En curso","variant":"secondary","tone":"progress"}`

#### CodeBlock

Código resaltado con copiar; sólo texto, no se ejecuta. title: archivo o comando.

- `code`: string (min 1, ≤8000)
- `language`: "text"|"ts"|"tsx"|"js"|"json"|"sql"|"bash"|"yaml"|"md"|"html"|"css"
- `title`?: string (min 1, ≤160) (null = por defecto)
- `lineNumbers`?: boolean (null = por defecto)

Ejemplo: `{"code":"const total = pagos.reduce((suma, p) => suma + p.monto, 0);","language":"ts","title":"totales.ts"}`

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

#### HoverCard

Un dato (label, subrayado punteado) que al pasar el cursor o enfocarlo con el teclado abre una tarjeta de sólo lectura: title, text y hasta 6 pares etiqueta–valor (items), como la ficha breve de una persona, un cliente o un término. No lleva hijos ni controles: para botones, campos o filtros en un panel usa Popover. La tarjeta sólo se abre con el cursor o el foco (no en táctil): no pongas ahí nada que no esté también en otro lugar de la vista. side elige dónde abre (bottom por omisión).

- `label`: string (min 1, ≤160)
- `title`?: string (min 1, ≤160) (null = por defecto)
- `text`?: string (min 1, ≤280) (null = por defecto)
- `items`?: [{ label: string (min 1, ≤160), value: string (min 1, ≤120) }] (min 1, máx 6) (null = por defecto)
- `side`?: "top"|"right"|"bottom"|"left"|null (null = por defecto)

Ejemplo: `{"label":"Ana López","title":"Ana López","text":"Arquitecta de Pai a cargo del proyecto.","items":[{"label":"Región","value":"Norte"},{"label":"Proyectos activos","value":"3"}]}`

#### IconTile

Icono en su cuadro (filas, tarjetas). label lo nombra; soft y solid toman el tone.

- `icon`: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"
- `label`: string (min 1, ≤160)
- `tone`?: "neutral"|"info"|"progress"|"success"|"warning"|"danger"|null (null = por defecto)
- `variant`?: "outline"|"elevated"|"soft"|"solid"|null (null = por defecto)
- `size`?: "sm"|"default"|"lg"|null (null = por defecto)

Ejemplo: `{"icon":"wallet","label":"Pagos","tone":"info","variant":"soft"}`

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

#### Rating

Calificación con estrellas, admite decimales. maxRating fija el total (5 por omisión); size elige sm, default o lg; showValue muestra el número. editable permite cambiar la calificación en estado local: nada se guarda. rating no puede superar maxRating.

- `rating`: number (≥0, ≤10)
- `maxRating`?: integer (≥1, ≤10) (null = por defecto)
- `size`?: "sm"|"default"|"lg"|null (null = por defecto)
- `showValue`?: boolean (null = por defecto)
- `editable`?: boolean (null = por defecto)

Ejemplo: `{"rating":4.5,"showValue":true}`

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

Gráfica con los colores del tema: bar, line, area o pie. categories es el eje X (o las porciones de pie) y cada serie trae un valor por categoría. pie usa una sola serie. Con kind bar, orientation horizontal dibuja barras acostadas (rankings, etiquetas largas). stacked apila las series en bar y area (totales por categoría); null o false las pone lado a lado, y en line o pie no cambia nada.

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

La tabla de datos de Portal y Console (DataTable): columnas tipadas (text, number, money en centavos alineado a la derecha, percent, date, badge, status con tono, link, person, progress), buscador, filtros «Etiqueta: valor» (filters[].key es la key de una columna o de cualquier celda que traen las filas, aunque no sea columna, p. ej. la de un secondaryKey), orden por columna (defaultSort.key, sólo columnas), paginación (pageSize; null la oculta y muestra todas las filas), selección (selectable añade casillas; selectionSummary deja sólo el pie «0 de N fila(s) seleccionada(s)», como la lista de proyectos), filas apagadas (muted) y un menú «⋯» por fila. Todo funciona dentro de la vista (filtra, ordena, pagina) y nada se guarda ni navega. Cada fila trae id y cells: { [key de columna]: valor }; una celda vacía es null.

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

#### FileList

Lista de archivos de una carpeta o un expediente, en filas (layout list, por omisión) o tarjetas (grid): nombre, tipo (pdf, document, sheet, slides, image, video, audio, code, archive u other: elige el icono), tamaño ya formateado («2.4 MB»), dueño y fecha de actualización (AAAA-MM-DD). Con href (ruta del Portal o https) el nombre enlaza; sin href es texto. No abre, descarga ni muestra el contenido de ningún archivo. Para la carpeta de Recursos de Pai usa Resources.

- `files`: [{ id: string (min 1, ≤80), name: string (min 1, ≤160), kind: "pdf"|"document"|"sheet"|"slides"|"image"|"video"|"audio"|"code"|"archive"|"other", size?: string (min 1, ≤20) (null = por defecto), owner?: string (min 1, ≤160) (null = por defecto), updated?: string (null = por defecto), href?: string (null = por defecto) }] (min 1, máx 200)
- `layout`?: "list"|"grid"|null (null = por defecto)

Ejemplo: `{"files":[{"id":"f1","name":"Propuesta comercial.pdf","kind":"pdf","size":"1.2 MB","owner":"Ana López","updated":"2026-10-02"},{"id":"f2","name":"Presupuesto 2027.xlsx","kind":"sheet","size":"84 KB","owner":"Luis Pérez","updated":"2026-09-28"},{"id":"f3","name":"Planos de la bodega.zip","kind":"archive","size":"24 MB","updated":"2026-09-15"}],"layout":"list"}`

#### Heatmap

Mapa de calor con los colores del tema: una matriz de filas × columnas (días × horas, semanas × días…) donde cada celda es más intensa cuanto mayor su valor. rows y columns son las etiquetas de los ejes; values trae una fila por cada fila, con un valor (0 o más) por columna. 0 se pinta vacío. La leyenda va de «Menos» a «Más» con el máximo; unit se añade a los valores. Las cifras se leen también sin el color (lectores de pantalla).

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `rows`: [string (min 1, ≤40)] (min 1, máx 31)
- `columns`: [string (min 1, ≤40)] (min 1, máx 60)
- `values`: [[number (≥0)]] (min 1, máx 31)
- `unit`?: string (≤20) (null = por defecto)

Ejemplo: `{"title":"Actividad del equipo por día y hora","rows":["Lun","Mar","Mié","Jue","Vie"],"columns":["9","11","13","15","17"],"values":[[4,7,2,6,3],[5,8,3,7,2],[3,6,1,9,4],[6,9,2,8,5],[2,4,0,3,1]],"unit":"tareas"}`

#### KeyValue

Pares etiqueta–valor (fechas, responsables, montos) en 1 a 3 columnas.

- `items`: [{ label: string (min 1, ≤160), value: string (min 1, ≤400) }] (min 1, máx 60)
- `columns`?: integer (≥1, ≤3) (null = por defecto)

Ejemplo: `{"items":[{"label":"Responsable","value":"Ana López"},{"label":"Inicio","value":"1 de septiembre de 2026"},{"label":"Presupuesto","value":"$420,000 MXN"}],"columns":3}`

#### Metric

Indicador (KPI): etiqueta, valor ya formateado («68 %», «$1.2 M»), unidad pequeña opcional («MXN») cambio opcional («+12 %», badge con trend) y detalle con su comparación o fecha de corte. tone colorea el valor: positive, warning, negative o info. icon añade un IconTile y trendLine una sparkline de 2–24 valores.

- `label`: string (min 1, ≤160)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `trendLine`?: [number] (min 2, máx 24) (null = por defecto)
- `value`: string (min 1, ≤40)
- `detail`?: string (≤160) (null = por defecto)
- `trend`?: "up"|"down"|"flat"|null (null = por defecto)
- `unit`?: string (min 1, ≤12) (null = por defecto)
- `delta`?: string (min 1, ≤12) (null = por defecto)
- `tone`?: "neutral"|"positive"|"warning"|"negative"|"info"|null (null = por defecto)

Ejemplo: `{"label":"Avance","value":"68 %","delta":"+12 pts","detail":"vs. agosto","trend":"up","tone":"positive"}`

#### Progress

Barra de avance de 0 a 100 con etiqueta opcional.

- `value`: number
- `max`?: number (null = por defecto)
- `label`?: string (null = por defecto)

Ejemplo: `{"value":68,"label":"Avance del proyecto"}`

#### ProgressRing

Anillo de avance de 0 a 100, con el valor al centro y la etiqueta debajo: para un indicador que se lee de un vistazo (avance de un hito, presupuesto usado). display reemplaza el texto del centro (p. ej. «5 de 8»); sin él se ve «68 %». description agrega una línea de apoyo. size elige sm, md (por omisión) o lg. Para varias barras en fila, usa Progress o BarList.

- `label`: string (min 1, ≤160)
- `value`: number (≥0, ≤100)
- `display`?: string (min 1, ≤20) (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)
- `size`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"label":"Avance del hito de pagos","value":68,"description":"Quedan la conciliación y las pruebas con el banco."}`

#### Stats

Fila de 1–6 KPIs: valor formateado, unidad, cambio con trend y tone y detalle. icon añade un IconTile; progress dibuja una barra de 0 a 100 con su etiqueta (label, «Avance» por omisión) y el porcentaje a la vista; trendLine dibuja una sparkline de 2–24 valores. variant elige row (fila dividida, por omisión) o cards (tarjetas en rejilla); dentro de Card siempre se usa row.

- `items`: [{ label: string (min 1, ≤160), value: string (min 1, ≤40), unit?: string (min 1, ≤12) (null = por defecto), delta?: string (min 1, ≤12) (null = por defecto), trend?: "up"|"down"|"flat"|null (null = por defecto), tone?: "neutral"|"positive"|"warning"|"negative"|"info"|null (null = por defecto), detail?: string (≤160) (null = por defecto), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), progress?: { value: number (≥0, ≤100), label?: string (min 1, ≤160) (null = por defecto) } (null = por defecto), trendLine?: [number] (min 2, máx 24) (null = por defecto) }] (min 1, máx 6)
- `variant`?: "row"|"cards"|null (null = por defecto)

Ejemplo: `{"items":[{"label":"Avance","icon":"chart","value":"68 %","delta":"+12 pts","trend":"up","tone":"positive"},{"label":"Cobrado","value":"$1.2 M","unit":"MXN","detail":"de $2.0 M","progress":{"value":60,"label":"Meta de cobro"}},{"label":"Hitos vencidos","trendLine":[5,4,3,1,2],"value":"2","delta":"+1","trend":"up","tone":"negative"}]}`

#### Table

Tabla de datos: columns son los encabezados y rows un arreglo de filas con una celda por columna.

- `columns`: [string (min 1, ≤160)] (min 1, máx 10)
- `rows`: [[string (≤640)]] (máx 200)
- `caption`?: string (≤160) (null = por defecto)

Ejemplo: `{"columns":["Hito","Responsable","Fecha"],"rows":[["Diseño","Ana López","12 sep"],["Desarrollo","Luis Pérez","30 oct"]],"caption":"Hitos del trimestre"}`

#### Tree

Árbol plegable (carpetas, módulos): nodos con id único y children, hasta 4 niveles y 200 nodos; expanded: ids abiertos; label: su nombre.

- `items`: [any] (min 1, máx 60)
- `expanded`?: [string (min 1, ≤60)] (máx 200) (null = por defecto)
- `label`?: string (min 1, ≤160) (null = por defecto)

Ejemplo: `{"items":[{"id":"docs","label":"Documentos","icon":"folder","children":[{"id":"sow","label":"SOW firmado","icon":"file-signature","badge":"v2"},{"id":"prd","label":"PRD","icon":"file"}]},{"id":"designs","label":"Diseños","icon":"folder"}],"expanded":["docs"],"label":"Carpetas del proyecto"}`

#### TreeTable

Tabla de árbol: las mismas columnas tipadas de DataTable (text, number, money en centavos, percent, date, badge, status, link, person, progress), pero cada fila puede traer children (hasta 3 niveles) que se despliegan bajo ella con su sangría: grupos por etapa o región con sus subtotales en las celdas del grupo, una lista de materiales, un organigrama. La primera columna lleva el botón de desplegar y siempre se ve (sin hideBelow). expanded: top (por omisión) abre el primer nivel, all todo, none nada. totals agrega un pie con el total general. search filtra y conserva los padres de lo que encuentra. Las columnas sortable ordenan entre hermanas. Todo pasa en la vista; nada se guarda ni navega.

- `columns`: [{ key: string, header: string (min 1, ≤160), sortable?: boolean (null = por defecto), hideBelow?: "sm"|"md"|"lg"|null (null = por defecto), type: "text"|"number"|"money"|"percent"|"date"|"badge"|"status"|"link"|"person"|"progress", secondaryKey?: string (null = por defecto), decimals?: integer (≥0, ≤4) (null = por defecto), currency?: string (min 3, ≤3) (null = por defecto), plusTax?: boolean (null = por defecto), format?: "day"|"instant"|"relative"|null (null = por defecto) }] (min 1, máx 10)
- `rows`: [{ id: string (min 1, ≤80), cells: object, muted?: boolean (null = por defecto), children?: [{ id: string (min 1, ≤80), cells: object, muted?: boolean (null = por defecto), children?: [{ id: string (min 1, ≤80), cells: object, muted?: boolean (null = por defecto) }] (min 1, máx 50) (null = por defecto) }] (min 1, máx 50) (null = por defecto) }] (min 1, máx 200)
- `expanded`?: "top"|"all"|"none"|null (null = por defecto)
- `search`?: string (min 1, ≤160) (null = por defecto)
- `totals`?: { label: string (min 1, ≤160), cells: object } (null = por defecto)

Ejemplo: `{"columns":[{"key":"name","header":"Etapa / proyecto","type":"text"},{"key":"owner","header":"Responsable","type":"person","hideBelow":"md"},{"key":"status","header":"Estado","type":"status"},{"key":"amount","header":"Monto","type":"money","currency":"MXN","sortable":true},{"key":"progress","header":"Avance","type":"progress","hideBelow":"sm"}],"rows":[{"id":"negociacion","cells":{"name":"Negociación","amount":60500000},"children":[{"id":"lumen","cells":{"name":"Portal de clientes · Grupo Lumen","owner":{"name":"Ana López","secondary":"Norte"},"status":{"label":"En revisión","tone":"progress"},"amount":42000000,"progress":60}},{"id":"nandu","cells":{"name":"App de rutas · Ñandú Logística","owner":{"name":"Luis Pérez","secondary":"Centro"},"status":{"label":"Propuesta enviada","tone":"info"},"amount":18500000,"progress":35}}]},{"id":"cierre","cells":{"name":"Cierre","amount":9900000},"children":[{"id":"alba","cells":{"name":"ERP de obra · Constructora Alba","owner":{"name":"Ana López","secondary":"Norte"},"status":{"label":"Firmada","tone":"success"},"amount":9900000,"progress":100}}]}],"expanded":"top","totals":{"label":"Total","cells":{"amount":70400000}}}`

### Grupo: Controles

#### ActionMenu

Menú de acciones que se abre al pulsar: sin label es el botón «⋯» de las filas y tarjetas; con label es un botón con flecha. Sus opciones son decorativas (no ejecutan nada).

- `label`?: string (min 1, ≤160) (null = por defecto)
- `items`: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), destructive?: boolean (null = por defecto), separatorBefore?: boolean (null = por defecto) }] (min 1, máx 20)
- `align`?: "start"|"end"|null (null = por defecto)

Ejemplo: `{"items":[{"label":"Editar","icon":"pencil"},{"label":"Duplicar","icon":"copy"},{"label":"Eliminar","icon":"trash","destructive":true,"separatorBefore":true}],"align":"end"}`

#### Autocomplete

Campo de texto que sugiere opciones mientras se escribe, con su etiqueta y ayuda: buscar un cliente, una ciudad o una persona entre items (2 a 50, { label, value }). Al elegir una opción el campo toma su texto; empty es el aviso cuando nada coincide («Sin resultados» por omisión). Responde dentro de la vista; nada se envía ni se guarda.

- `label`?: string (min 1, ≤160) (null = por defecto)
- `description`?: string (≤160) (null = por defecto)
- `placeholder`?: string (≤80) (null = por defecto)
- `items`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 50)
- `empty`?: string (min 1, ≤80) (null = por defecto)

Ejemplo: `{"label":"Cliente","placeholder":"Busca un cliente…","items":[{"label":"Grupo Lumen","value":"lumen"},{"label":"Ñandú Logística","value":"nandu"},{"label":"Constructora Alba","value":"alba"}]}`

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

#### DateSelector

Filtro de fecha de reUI en un botón con calendario: al abrirlo se elige un día o un rango (o un mes, trimestre, semestre o año si periodTypes los ofrece) y un operador (Es, Hasta, Desde, Entre); «Aplicar» cambia el texto del botón. value es el filtro al cargar, de días: { operator, start, end? } en AAAA-MM-DD (end sólo con between). allowRange false quita «Entre»; presetMode fija un operador; showTwoMonths muestra dos meses en pantallas anchas. label nombra el filtro («Fecha de cierre»). Responde dentro de la vista; nada filtra, se envía ni se guarda.

- `label`?: string (min 1, ≤160) (null = por defecto)
- `value`?: { operator: "is"|"before"|"after"|"between", start: string, end?: string (null = por defecto) } (null = por defecto)
- `allowRange`?: boolean (null = por defecto)
- `periodTypes`?: ["day"|"month"|"quarter"|"half-year"|"year"] (min 1, máx 5) (null = por defecto)
- `defaultPeriodType`?: "day"|"month"|"quarter"|"half-year"|"year"|null (null = por defecto)
- `presetMode`?: "is"|"before"|"after"|"between"|null (null = por defecto)
- `showTwoMonths`?: boolean (null = por defecto)

Ejemplo: `{"label":"Fecha de cierre","value":{"operator":"between","start":"2026-10-01","end":"2026-10-31"}}`

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

#### Popover (admite hijos)

Panel flotante que abre un botón con label e icon opcional. Sus hijos contienen filtros o detalles y title añade un título dentro del panel. side elige dónde abre (bottom por omisión). Los cambios quedan en la vista: nada se envía ni se guarda.

- `label`: string (min 1, ≤160)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `title`?: string (≤80) (null = por defecto)
- `side`?: "top"|"right"|"bottom"|"left"|null (null = por defecto)

Ejemplo: `{"label":"Ver filtros","icon":"filter","title":"Filtrar entregables"}`

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

### Grupo: Formularios

#### Cascader

Selector de maqueta para un valor dentro de un árbol de hasta 3 niveles, con su etiqueta: región › estado › ciudad, área › equipo › rol, categoría › servicio. items son los nodos de primer nivel { value, label, children? } (1 a 30 por nivel, value único en todo el árbol); value es el value de una hoja (un nodo sin children) y el campo muestra su ruta («México / Jalisco / Guadalajara»); placeholder es el texto mientras no hay valor. Se ve como en Pai pero está deshabilitado: no se abre y nada se envía ni se guarda.

- `label`: string (min 1, ≤160)
- `items`: [{ value: string (min 1, ≤80), label: string (min 1, ≤160), children?: [{ value: string (min 1, ≤80), label: string (min 1, ≤160), children?: [{ value: string (min 1, ≤80), label: string (min 1, ≤160) }] (min 1, máx 30) (null = por defecto) }] (min 1, máx 30) (null = por defecto) }] (min 1, máx 30)
- `value`?: string (min 1, ≤80) (null = por defecto)
- `placeholder`?: string (min 1, ≤80) (null = por defecto)

Ejemplo: `{"label":"Sede del proyecto","placeholder":"Elige una ciudad","value":"gdl","items":[{"value":"mx","label":"México","children":[{"value":"jal","label":"Jalisco","children":[{"value":"gdl","label":"Guadalajara"},{"value":"zap","label":"Zapopan"}]},{"value":"nl","label":"Nuevo León","children":[{"value":"mty","label":"Monterrey"}]}]},{"value":"co","label":"Colombia","children":[{"value":"ant","label":"Antioquia","children":[{"value":"med","label":"Medellín"}]}]}]}`

#### Combobox

Campo de maqueta que en Pai se escribe para filtrar una lista y elegir una opción, con su etiqueta: responsable, cliente, servicio. options son las opciones (2 a 50, { label, value }); value es el value de la elegida (su texto aparece en el campo); placeholder, el texto mientras no hay valor. Se ve como en Pai pero está deshabilitado: no se abre y nada se envía ni se guarda.

- `label`: string (min 1, ≤160)
- `options`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 50)
- `value`?: string (min 1, ≤80) (null = por defecto)
- `placeholder`?: string (min 1, ≤80) (null = por defecto)

Ejemplo: `{"label":"Responsable","placeholder":"Busca a una persona…","value":"lucia","options":[{"label":"Lucía Herrera","value":"lucia"},{"label":"Mateo Ríos","value":"mateo"},{"label":"Valeria Campos","value":"valeria"}]}`

#### InputOTP

Casillas de un código corto que no es secreto, de maqueta y con su etiqueta: el folio de una cita, el código de una sala o de una invitación. length es el número de casillas (4 a 8); value, dígitos de ejemplo (a lo más length) o nada para dejarlas vacías. Es sólo visual: está deshabilitado, no autocompleta y nada se envía. Nunca la uses para contraseñas, PIN ni códigos de verificación: un formulario de maqueta no los pide.

- `label`: string (min 1, ≤160)
- `length`: integer (≥4, ≤8)
- `value`?: string (≤8) (null = por defecto)

Ejemplo: `{"label":"Código de la sala","length":6,"value":"4821"}`

#### NumberField

Campo numérico de maqueta con botones − y + a los lados y su etiqueta: cantidad de licencias, horas estimadas, porcentaje de anticipo. value es el número que muestra; min, max y step acotan el rango (value dentro de él); unit es la unidad corta que va a la derecha («horas», «%», «MXN»). Se ve como en Pai pero está deshabilitado: no se escribe en él y nada se envía ni se guarda.

- `label`: string (min 1, ≤160)
- `value`?: number (null = por defecto)
- `min`?: number (null = por defecto)
- `max`?: number (null = por defecto)
- `step`?: number (null = por defecto)
- `unit`?: string (min 1, ≤16) (null = por defecto)

Ejemplo: `{"label":"Horas estimadas","value":24,"min":0,"max":200,"step":4,"unit":"horas"}`

#### PhoneInput

Campo de teléfono de maqueta con su etiqueta: el prefijo del país (country: MX, US, CO, AR, CL, PE, GT, ES; MX por omisión) y el número ya formateado («55 1234 5678»). Es una maqueta: no valida el número ni lo envía, y está deshabilitado. No escribas el número real de una persona; usa uno de ejemplo o déjalo vacío con placeholder.

- `label`: string (min 1, ≤160)
- `country`?: "MX"|"US"|"CO"|"AR"|"CL"|"PE"|"GT"|"ES"|null (null = por defecto)
- `value`?: string (≤20) (null = por defecto)
- `placeholder`?: string (min 1, ≤40) (null = por defecto)

Ejemplo: `{"label":"Teléfono de contacto","country":"MX","placeholder":"55 0000 0000"}`

#### SignaturePad

Espacio para firmar en un formulario de maqueta: su etiqueta, la línea de firma con «Firma aquí» y una nota opcional bajo la línea («Nombre y firma del representante»). Siempre está vacío: no captura trazos, no guarda nada y nunca dice que algo esté firmado. No escribas ahí nombres de quien firmó ni fechas de firma.

- `label`: string (min 1, ≤160)
- `note`?: string (min 1, ≤80) (null = por defecto)

Ejemplo: `{"label":"Firma del cliente","note":"Nombre y firma del representante legal"}`

#### Slider

Deslizador de maqueta con su etiqueta: un presupuesto, un porcentaje de avance, un rango de precios. value es un número o un rango [desde, hasta] (desde ≤ hasta); min y max acotan la barra (0 y 100 por omisión, value dentro); step es el paso; unit, la unidad del valor que se lee junto a la etiqueta: «%» o «días» lo acompañan, y un código de moneda ISO («MXN», «USD») le da formato de moneda («MXN 40,000.00»). Se ve como en Pai pero está deshabilitado: no se mueve y nada se envía ni se guarda.

- `label`: string (min 1, ≤160)
- `value`: number | array
- `min`?: number (null = por defecto)
- `max`?: number (null = por defecto)
- `step`?: number (null = por defecto)
- `unit`?: string (min 1, ≤16) (null = por defecto)

Ejemplo: `{"label":"Rango de presupuesto","value":[40000,120000],"min":0,"max":200000,"step":5000,"unit":"MXN"}`

#### TimePicker

Selector de hora de maqueta con su etiqueta: la hora de una junta, de una entrega o de un corte. value es la hora en formato HH:mm de 24 h («14:30») aunque hourCycle 12 la muestre como «02:30 p. m.»; minuteStep es el paso de los minutos (15 da 00, 15, 30, 45) y min y max acotan las horas (HH:mm, value entre ellos). Se ve como en Pai pero está deshabilitado: no se abre y nada se envía ni se guarda.

- `label`: string (min 1, ≤160)
- `value`?: string (null = por defecto)
- `hourCycle`?: number | number (null = por defecto)
- `minuteStep`?: integer (≥1, ≤30) (null = por defecto)
- `min`?: string (null = por defecto)
- `max`?: string (null = por defecto)

Ejemplo: `{"label":"Hora de la revisión","value":"10:30","hourCycle":24,"minuteStep":15,"min":"09:00","max":"18:00"}`

### Grupo: Conversación

#### ChatComposer

El cuadro donde se escribe un mensaje a un agente, de maqueta: no se conecta a ningún agente ni envía mensajes. Se pinta deshabilitado, con los botones de adjuntar y enviar decorativos (también deshabilitados). placeholder es el texto de ayuda; value, un borrador de ejemplo; attachments, nombres de archivos ya adjuntos (sin enlace). Va al pie de ChatLayout o debajo de un ChatThread. Nunca pidas contraseñas, tarjetas ni códigos.

- `placeholder`?: string (min 1, ≤160) (null = por defecto)
- `value`?: string (≤2000) (null = por defecto)
- `attachments`?: [string (min 1, ≤160)] (máx 5) (null = por defecto)

Ejemplo: `{"placeholder":"Pregunta sobre el proyecto…","attachments":["Acta revisión 2026-10-02.pdf"]}`

#### ChatThread

Hilo de una conversación, de sólo lectura y de maqueta: no se conecta a ningún agente ni envía mensajes. Cada mensaje lleva id (único), role (user a la derecha, assistant a la izquierda con su avatar, system centrado y discreto), author opcional (sin él: «Tú» o «Asistente»), at opcional (instante ISO), text en texto plano (sin Markdown, HTML ni enlaces), attachments (nombres de archivo, sin enlace) y steps del agente (label y status done, running o error). Usa sólo mensajes que te dio una herramienta o el usuario; no inventes lo que dijo una persona.

- `messages`: [{ id: string (min 1, ≤80), role: "user"|"assistant"|"system", author?: string (min 1, ≤160) (null = por defecto), at?: string (null = por defecto), text: string (≤2000), attachments?: [string (min 1, ≤160)] (máx 10) (null = por defecto), steps?: [{ label: string (min 1, ≤160), status: "done"|"running"|"error" }] (máx 12) (null = por defecto) }] (min 1, máx 60)

Ejemplo: `{"messages":[{"id":"m1","role":"user","author":"Ana Torres","at":"2026-10-06T16:02:00Z","text":"¿Cómo va el hito de pagos del portal de proveedores?"},{"id":"m2","role":"assistant","at":"2026-10-06T16:02:10Z","text":"El hito «Pagos a proveedores» va al 68 %: quedan la conciliación y las pruebas con el banco. La entrega sigue para el 28 de octubre.","steps":[{"label":"Leí el plan del proyecto","status":"done"},{"label":"Revisé las tareas abiertas","status":"done"}]},{"id":"m3","role":"user","author":"Ana Torres","at":"2026-10-06T16:04:00Z","text":"Te paso el acta de la última revisión.","attachments":["Acta revisión 2026-10-02.pdf"]}]}`

### Grupo: Navegación

#### Breadcrumb

Migas de pan: dónde está la pantalla («Proyectos › Portenta › Cronograma»). El último elemento es la página actual; los anteriores pueden llevar href.

- `items`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 8)

Ejemplo: `{"items":[{"label":"Proyectos","href":"/organization/projects"},{"label":"Portenta"},{"label":"Cronograma"}]}`

#### Menubar

Barra de menús de una app de escritorio o editor: hasta 6 menús (Archivo, Editar, Ver…), cada uno con 1 a 12 opciones con su atajo opcional («⌘ S») y una línea antes (separatorBefore). Los menús se abren dentro de la vista; las opciones son decorativas: no ejecutan nada ni navegan.

- `menus`: [{ label: string (min 1, ≤160), items: [{ label: string (min 1, ≤160), shortcut?: string (min 1, ≤20) (null = por defecto), separatorBefore?: boolean (null = por defecto) }] (min 1, máx 12) }] (min 1, máx 6)

Ejemplo: `{"menus":[{"label":"Archivo","items":[{"label":"Nuevo documento","shortcut":"⌘ N"},{"label":"Exportar como PDF","separatorBefore":true}]},{"label":"Editar","items":[{"label":"Deshacer","shortcut":"⌘ Z"},{"label":"Rehacer","shortcut":"⇧ ⌘ Z"}]}]}`

#### NavigationMenu

Navegación horizontal de un sitio o app. Cada item lleva href para un enlace directo o items para un submenú de 2–8 enlaces con descripción opcional, nunca ambos. Los href navegan sólo a rutas del Portal o https; los enlaces del submenú sin href quedan inertes. Hasta 6 entradas principales.

- `items`: [{ label: string (min 1, ≤160), href?: string (null = por defecto), items?: [{ label: string (min 1, ≤160), href?: string (null = por defecto), description?: string (≤120) (null = por defecto) }] (min 2, máx 8) (null = por defecto) }] (min 1, máx 6)

Ejemplo: `{"items":[{"label":"Proyectos","href":"/organization/projects"},{"label":"Recursos","items":[{"label":"Entregables","href":"/resources/entregables","description":"Documentos y avances compartidos."},{"label":"Guías","description":"Material de apoyo para el equipo."}]}]}`

#### OrgSwitcher

El selector de organización de Portal, solo: muestra la organización (o Pai sin organization) y se abre con «Buscar…», Pai, Consola (staff) y «Tus organizaciones». Filtra al escribir; elegir no cambia nada.

- `organization`?: string (min 1, ≤160) (null = por defecto)
- `organizations`?: [string (min 1, ≤160)] (máx 20) (null = por defecto)
- `staff`?: boolean (null = por defecto)

Ejemplo: `{"organization":"Portenta","organizations":["Portenta","Grupo Lumen","Ñandú Logística"],"staff":true}`

#### PageBar

La barra superior de una página de Portal o Console, sola: botón del menú lateral, migas, acciones a la derecha (botones decorativos). assistant está obsoleta y no muestra nada. Úsala para mostrar la barra fuera de un PortalShell/ConsoleShell (que ya la traen).

- `breadcrumb`: [{ label: string (min 1, ≤160), href?: string (null = por defecto) }] (min 1, máx 6)
- `actions`?: [string (min 1, ≤160)] (máx 3) (null = por defecto)
- `assistant`?: boolean (null = por defecto)

Ejemplo: `{"breadcrumb":[{"label":"Proyectos","href":"/organization/projects"},{"label":"CRM comercial"}],"actions":["Exportar"]}`

#### PageHeader

Encabezado de una página de producto, como los de Portal y Console: back (enlace de regreso, «← Todos los proyectos»), icon (en su cuadro), eyebrow (antetítulo), title, description, badges (estados con tono), meta (datos breves con icono: «Activo», «Por asignar», «Actualizado 6 oct») y hasta 3 actions a la derecha (la primera sólida, las demás con borde; con href navegan). level h2 lo usa como encabezado de una sección de la página. Úsalo en la región header de PageLayout o DetailLayout; para un proyecto de Portal, ProjectHeader.

- `back`?: { label: string (min 1, ≤160), href?: string (null = por defecto) } (null = por defecto)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `eyebrow`?: string (min 1, ≤60) (null = por defecto)
- `title`: string (min 1, ≤160)
- `level`?: "h1"|"h2"|null (null = por defecto)
- `description`?: string (≤2000) (null = por defecto)
- `badges`?: [{ label: string (min 1, ≤160), tone: "neutral"|"info"|"progress"|"success"|"warning"|"danger" }] (min 1, máx 4) (null = por defecto)
- `meta`?: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto) }] (min 1, máx 4) (null = por defecto)
- `actions`?: [{ label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) }] (min 1, máx 3) (null = por defecto)

Ejemplo: `{"back":{"label":"Todos los proyectos","href":"/organization/projects"},"icon":"folder","title":"Pai Ecosystem","description":"Lo que se decidió en el proyecto, por qué y qué partes lo componen.","badges":[{"label":"Activo","tone":"success"}],"meta":[{"label":"Por asignar","icon":"user"},{"label":"Actualizado 6 oct 2026","icon":"calendar"}],"actions":[{"label":"Nuevo nodo","icon":"plus"},{"label":"Ver en toda la organización"}]}`

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

Estado vacío de una sección, como en Portal: icono, «Aún no hay {objetos}», una línea para quien mira y una acción opcional (botón con href o decorativo). illustration elige tile (por omisión) o stack (IconStack); secondaryAction añade una segunda acción con borde.

- `title`: string (min 1, ≤160)
- `description`?: string (≤2000) (null = por defecto)
- `icon`?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto)
- `action`?: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) } (null = por defecto)
- `illustration`?: "tile"|"stack"|null (null = por defecto)
- `secondaryAction`?: { label: string (min 1, ≤160), icon?: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key"|"flag"|"file-signature"|"list-checks"|"network"|"book-open"|"package"|"orbit"|"shield"|"monitor-smartphone"|"plus"|"download"|"upload"|"filter"|"send"|"pencil"|"trash"|"copy"|"external"|"sparkles"|"check"|"clock"|"id-card"|"receipt-text"|"folder-kanban"|"file-cog"|"layout-grid"|"log-in"|"graduation-cap"|null (null = por defecto), href?: string (null = por defecto) } (null = por defecto)

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

#### EventCalendar

Calendario de eventos de reUI para la agenda de un cliente o un equipo: events con id, title, start y end y allDay. Un evento de todo el día usa días AAAA-MM-DD con end incluido (start 2026-11-11 y end 2026-11-12 son dos días); uno con hora usa instantes ISO con zona («2026-11-04T10:00:00-06:00») y end es la hora en que termina. view abre en month (por omisión), week, day o agenda; date es el día al que abre y height su alto (sm, md por omisión, lg). Se navega y se cambia de vista; nada se arrastra, se crea ni se guarda. Para las fechas de entrega de un proyecto de Pai usa MilestoneTimeline.

- `events`: [{ id: string (min 1, ≤80), title: string (min 1, ≤160), start: string, end: string, allDay?: boolean (null = por defecto) }] (máx 200)
- `view`?: "month"|"week"|"day"|"agenda"|null (null = por defecto)
- `date`?: string (null = por defecto)
- `height`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"events":[{"id":"e1","title":"Revisión de diseño","start":"2026-11-04T10:00:00-06:00","end":"2026-11-04T11:00:00-06:00"},{"id":"e2","title":"Entrega de wireframes","start":"2026-11-06","end":"2026-11-06","allDay":true},{"id":"e3","title":"Taller con el cliente","start":"2026-11-11","end":"2026-11-12","allDay":true}],"view":"month","date":"2026-11-01"}`

#### Gantt

Diagrama de Gantt de reUI para el plan de un cliente (para los hitos de un proyecto de Pai usa MilestoneTimeline): resources es el árbol de filas a la izquierda (hasta 3 niveles: fase, tarea, subtarea) y events las barras, cada una en su fila (resourceId), con start y end (AAAA-MM-DD, end incluido), progress de 0 a 100, milestone (un rombo en start), dependencies (ids de las barras que la preceden, con flecha) y la línea base planeada (baselineStart y baselineEnd). scale (day, week, month por omisión, quarter o year) y date (el día al que abre) eligen la vista; height su alto (sm, md por omisión, lg). Se navega y se cambia de escala; nada se arrastra ni se guarda.

- `resources`: [{ id: string (min 1, ≤80), title: string (min 1, ≤160), children?: [{ id: string (min 1, ≤80), title: string (min 1, ≤160), children?: [{ id: string (min 1, ≤80), title: string (min 1, ≤160) }] (min 1, máx 30) (null = por defecto) }] (min 1, máx 30) (null = por defecto) }] (min 1, máx 30)
- `events`: [{ id: string (min 1, ≤80), title: string (min 1, ≤160), resourceId: string (min 1, ≤80), start: string, end: string, progress?: number (≥0, ≤100) (null = por defecto), milestone?: boolean (null = por defecto), dependencies?: [string (min 1, ≤80)] (máx 10) (null = por defecto), baselineStart?: string (null = por defecto), baselineEnd?: string (null = por defecto) }] (máx 200)
- `scale`?: "day"|"week"|"month"|"quarter"|"year"|null (null = por defecto)
- `date`?: string (null = por defecto)
- `height`?: "sm"|"md"|"lg"|null (null = por defecto)

Ejemplo: `{"resources":[{"id":"diseno","title":"Diseño","children":[{"id":"wireframes","title":"Wireframes"},{"id":"visual","title":"Diseño visual"}]},{"id":"desarrollo","title":"Desarrollo","children":[{"id":"api","title":"API de pedidos"}]}],"events":[{"id":"e1","title":"Wireframes","resourceId":"wireframes","start":"2026-11-02","end":"2026-11-13","progress":100},{"id":"e2","title":"Diseño visual","resourceId":"visual","start":"2026-11-16","end":"2026-11-27","progress":40,"dependencies":["e1"]},{"id":"e3","title":"API de pedidos","resourceId":"api","start":"2026-11-23","end":"2026-12-11","progress":10,"dependencies":["e1"]},{"id":"e4","title":"Entrega a revisión","resourceId":"api","start":"2026-12-14","end":"2026-12-14","milestone":true}],"scale":"month","date":"2026-11-02"}`

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

El Cronograma real de Portal: hitos como barras en el tiempo (con avance, responsable, monto y estado de pago), sus tareas, dependencias y línea base, y el panel de detalle al elegir uno. Se puede cambiar la escala, el zoom y las columnas, y abrir hitos y tareas; nada se guarda ni navega. Fechas AAAA-MM-DD; today fija el día de hoy (por defecto, el actual). selected abre un hito al cargar. staff es el de Console: «Nuevo hito» en la barra y los botones de editar y eliminar del detalle, inertes. Trae su propio marco (framed ya no cambia nada).

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

#### Stepper (admite hijos)

Pasos navegables: un hijo por paso, en orden; current (desde 1) abre uno. Sin contenido usa Stages.

- `steps`: [{ title: string (min 1, ≤160), description?: string (≤80) (null = por defecto) }] (min 2, máx 8)
- `current`?: integer (≥1, ≤8) (null = por defecto)
- `orientation`?: "horizontal"|"vertical"|null (null = por defecto)

Ejemplo: `{"steps":[{"title":"Datos","description":"Empresa y contacto"},{"title":"Alcance"},{"title":"Confirmar"}],"current":2}`

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

### Grupo: Comercio

#### ComparisonTable

Tabla comparativa de un cliente: plans son las columnas (2 a 5) y cada fila de rows lleva feature y un valor por plan: true (✓ incluido), false (✗ no incluido) o un texto corto («Hasta 5», «Por uso»). highlighted resalta la columna de un plan por su nombre. caption describe la tabla. Es informativa: sin precios de Pai, formularios ni datos de pago; usa sólo datos del cliente o de una herramienta.

- `caption`?: string (≤2000) (null = por defecto)
- `plans`: [string (min 1, ≤40)] (min 2, máx 5)
- `highlighted`?: string (min 1, ≤40) (null = por defecto)
- `rows`: [{ feature: string (min 1, ≤160), values: [boolean | string (min 1, ≤40)] }] (min 1, máx 30)

Ejemplo: `{"caption":"Qué incluye cada plan","plans":["Básico","Clínica","Red"],"highlighted":"Clínica","rows":[{"feature":"Agenda en línea","values":[true,true,true]},{"feature":"Sucursales","values":["1","Hasta 5","Ilimitadas"]},{"feature":"Reportes mensuales","values":[false,true,true]},{"feature":"Soporte dedicado","values":[false,false,true]}]}`

#### PricingGrid

Tarjetas de planes de un cliente (2 a 4): name, price en texto ya formateado («$1,490 MXN», «A cotizar»), period opcional («al mes»), description, features (lo que incluye) y cta, el texto de un botón que se pinta deshabilitado. highlighted resalta un plan (a lo más uno) con «Recomendado». Los precios son contenido del cliente (también dentro del sitio de pai.lat): nunca los presentes como precios de Pai ni inventes cifras, y ningún plan puede nombrar a Pai; úsalos sólo si vienen de sus datos o de una herramienta. Es informativo: nada se compra, cobra ni envía, y no lleva formularios ni datos de pago.

- `plans`: [{ name: string (min 1, ≤160), price: string (min 1, ≤40), period?: string (min 1, ≤40) (null = por defecto), description?: string (≤2000) (null = por defecto), features: [string (min 1, ≤160)] (máx 12), highlighted?: boolean (null = por defecto), cta?: string (min 1, ≤40) (null = por defecto) }] (min 2, máx 4)

Ejemplo: `{"plans":[{"name":"Básico","price":"$490 MXN","period":"al mes","description":"Para una sucursal.","features":["Agenda en línea","Recordatorios por correo"],"cta":"Elegir Básico"},{"name":"Clínica","price":"$1,490 MXN","period":"al mes","description":"Para varias sucursales y su equipo.","features":["Todo lo de Básico","Hasta 5 sucursales","Reportes mensuales"],"highlighted":true,"cta":"Elegir Clínica"},{"name":"Red","price":"A cotizar","features":["Sucursales ilimitadas","Soporte dedicado"],"cta":"Hablar con ventas"}]}`

#### ReviewList

Lista de reseñas de los clientes de un cliente: author, rating de 0 a 5 (admite medios), text, at opcional (AAAA-MM-DD) y source. Usa sólo citas y calificaciones que vengan de datos del cliente o de una herramienta: no inventes testimonios, nombres ni estrellas. source dice de dónde salen (p. ej. «Encuesta NPS sep 2026», «Google Reviews»); sin source, el item se marca «Ejemplo» y no se presenta como real. Sólo lectura: nada se publica ni responde.

- `reviews`: [{ author: string (min 1, ≤160), rating: number (≥0, ≤5), text: string (≤2000), at?: string (null = por defecto), source?: string (min 2, ≤60) (null = por defecto) }] (min 1, máx 20)

Ejemplo: `{"reviews":[{"author":"Mariana López","rating":5,"text":"Agendar mi cita me tomó un minuto y me llegó el recordatorio un día antes.","at":"2026-09-14","source":"Google Reviews"},{"author":"Jorge Ramírez","rating":4,"text":"Muy buena atención; me gustaría poder cambiar la cita desde el correo.","at":"2026-09-02","source":"Encuesta NPS sep 2026"}]}`

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

## Recetas

Pantallas armadas de punta a punta (`view_catalog` con `recipe`). Copia la receta más cercana, cambia los datos por los de las tools y quita lo que sobre.

### dashboard

Tablero de una app: KPIs, gráfica, ranking lateral y tabla al pie.

Tablero de la app de un cliente: AppShell como raíz y DashboardLayout con Stats en kpis, Chart en main, BarList en side y DataTable en footer. Cambia los datos por los que trajeron las herramientas (con su fecha de corte) y quita las regiones que no uses con regions.

```json
{"root":"app","elements":{"app":{"type":"AppShell","props":{"brand":{"name":"Portenta","detail":"Ventas"},"nav":[{"label":"Tablero","icon":"dashboard","active":true},{"label":"Clientes","icon":"users"}],"title":"Tablero comercial"},"children":["tablero"]},"tablero":{"type":"DashboardLayout","props":{"side":"narrow"},"children":["kpis","grafica","ranking","tabla"]},"kpis":{"type":"Stats","props":{"items":[{"label":"Ventas del mes","value":"$1.8 M","delta":"+12 %","trend":"up","tone":"positive"},{"label":"Oportunidades","value":"42","detail":"al 30 sep 2026"},{"label":"Ticket medio","value":"$43 K","delta":"-3 %","trend":"down","tone":"warning"}]}},"grafica":{"type":"Chart","props":{"title":"Ventas por mes","kind":"bar","categories":["Jul","Ago","Sep"],"series":[{"name":"Ventas","values":[1.4,1.6,1.8]}],"unit":"M"}},"ranking":{"type":"BarList","props":{"items":[{"label":"Ana López","value":640},{"label":"Luis Pérez","value":410}]}},"tabla":{"type":"DataTable","props":{"columns":[{"key":"cliente","header":"Cliente","type":"text"},{"key":"monto","header":"Monto","type":"money"}],"rows":[{"id":"r1","cells":{"cliente":"Grupo Lumen","monto":42000000}},{"id":"r2","cells":{"cliente":"Ñandú Logística","monto":18500000}}]}}}}
```

### list-filters

Lista con encabezado, filtros y tabla: la pantalla de una sección.

Pantalla de lista (proyectos, clientes, pedidos): PageLayout con PageHeader en header, FilterBar en toolbar y DataTable (o TreeTable si hay grupos) en main. Va en la raíz o dentro de un shell (PortalShell, ConsoleShell, AppShell).

```json
{"root":"pagina","elements":{"pagina":{"type":"PageLayout","props":{"regions":["header","toolbar","main"]},"children":["encabezado","filtros","tabla"]},"encabezado":{"type":"PageHeader","props":{"title":"Clientes","description":"Cuentas activas y su responsable.","actions":[{"label":"Nuevo cliente","icon":"plus"}]}},"filtros":{"type":"FilterBar","props":{"search":"Buscar cliente…","filters":[{"label":"Región","value":"Todas","options":["Todas","Norte","Centro"]}]}},"tabla":{"type":"DataTable","props":{"columns":[{"key":"cliente","header":"Cliente","type":"text","sortable":true},{"key":"estado","header":"Estado","type":"status"}],"rows":[{"id":"c1","cells":{"cliente":"Grupo Lumen","estado":{"label":"Activo","tone":"success"}}},{"id":"c2","cells":{"cliente":"Constructora Alba","estado":{"label":"En pausa","tone":"warning"}}}],"pageSize":10}}}}
```

### record-detail

Detalle de un registro: encabezado, datos clave, pestañas y lateral.

Pantalla de detalle (un cliente, un pedido, un contrato): DetailLayout con PageHeader en header, KeyValue en summary, Tabs en main (una pestaña por hijo: Timeline, Text, DataTable) e Item en aside.

```json
{"root":"detalle","elements":{"detalle":{"type":"DetailLayout","props":{},"children":["encabezado","datos","pestanas","lateral"]},"encabezado":{"type":"PageHeader","props":{"back":{"label":"Clientes"},"title":"Grupo Lumen","badges":[{"label":"Activo","tone":"success"}]}},"datos":{"type":"KeyValue","props":{"items":[{"label":"Responsable","value":"Ana López"},{"label":"Región","value":"Norte"},{"label":"Cliente desde","value":"mar 2024"}],"columns":3}},"pestanas":{"type":"Tabs","props":{"tabs":[{"label":"Actividad","value":"actividad"},{"label":"Notas","value":"notas"}],"defaultValue":"actividad"},"children":["actividad","notas"]},"actividad":{"type":"Timeline","props":{"items":[{"date":"2 oct","title":"Propuesta enviada","status":"done"},{"date":"9 oct","title":"Revisión con dirección","status":"current"}]}},"notas":{"type":"Text","props":{"text":"Prefiere reuniones los martes."}},"lateral":{"type":"Item","props":{"title":"Contrato marco.pdf","description":"Firmado el 15 mar 2024","icon":"file"}}}}
```

### list-reading

Lista y lectura: elementos a la izquierda y el elegido a la derecha.

Bandeja o revisión (solicitudes, mensajes, incidencias): SplitView con un Stack de Item en list y DetailSheet en línea en detail (antetítulo, título, estados y sus hijos). Elegir en la lista no cambia el detalle: la vista es estática.

```json
{"root":"bandeja","elements":{"bandeja":{"type":"SplitView","props":{"listWidth":"medium"},"children":["lista","lectura"]},"lista":{"type":"Stack","props":{"direction":"vertical","gap":"sm"},"children":["s1","s2"]},"s1":{"type":"Item","props":{"title":"Cambio de alcance","description":"Grupo Lumen","meta":"hoy"}},"s2":{"type":"Item","props":{"title":"Factura pendiente","description":"Ñandú Logística","meta":"ayer"}},"lectura":{"type":"DetailSheet","props":{"eyebrow":"Solicitud","title":"Cambio de alcance","badges":[{"label":"En revisión","tone":"progress"}]},"children":["texto"]},"texto":{"type":"Text","props":{"text":"El cliente pide sumar el módulo de reportes a la fase 2."}}}}
```

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
