---
name: views
description: UI generativa de Pai (catálogo pai-view@1, 54 componentes del sistema de diseño de Pai). Dibuja vistas en la conversación con view_render (dashboards, comparativos, resúmenes visuales de datos ya obtenidos) o guárdalas en Recursos como bloque view de una page canvas (tableros, mockups de pantallas con AppShell, reportes visuales). Úsalo cuando pidan ver, mostrar, graficar o comparar datos de Pai de forma visual, un tablero, dashboard, mockup, wireframe o pantalla de una app, o editar una vista existente.
argument-hint: "[proyecto] [qué vista: tablero, pantalla, comparativo…]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# UI generativa de Pai (`pai-view@1`)

Lee antes el skill `pai-console`: entorno, descubrimiento, buscar antes de crear, CAS.

**Catálogo completo**, generado desde el código: `${CLAUDE_PLUGIN_ROOT}/skills/views/references/view-catalog.md`. Tiene los 54 componentes con sus props, límites e iconos. `view_catalog` devuelve lo mismo desde el servidor.

## Tres formas en que aparece una vista

| Forma | Cuándo | Cómo |
|---|---|---|
| **Automática** | Toda tool de lectura (`timeline_get`, `payment_list`, `task_board`, `knowledge_view`…) | En los hosts con MCP Apps, su resultado ya se dibuja solo como una vista de Pai. **No lo repitas** con `view_render` ni con tablas en texto: comenta lo importante |
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
- **Tienen hijos** solo AppShell, Stack, Grid, Section, Card, Collapsible, Tabs, UnderlinedTabs, Tooltip y ButtonGroup.
  - Tabs y UnderlinedTabs llevan un hijo por pestaña, en orden; normalmente cada hijo es un Stack.
  - Tooltip lleva un solo hijo, no interactivo.
- **Props estrictas:** solo las del catálogo. Nada de `className`, `style`, colores, HTML ni expresiones. Las props que admiten `null` se pueden omitir.
- **Iconos:** solo los del catálogo, por ejemplo `home`, `users`, `calendar`, `wallet`, `receipt`, `reports`, `book-open`, `plus`, `download`, `check`. La lista completa está en la referencia.
- Límites: ≤300 elementos y ≤12 niveles; `Grid` de 1 a 6 columnas; `Table` ≤10 columnas y ≤200 filas; `Chart` ≤6 series y ≤60 categorías.

## Qué componente usar

| Necesito… | Usa | No uses |
|---|---|---|
| Un KPI | `Metric`, con `unit` y `tone` (`positive`, `warning`, `negative`, `info`) | Texto suelto con la cifra |
| El estado de algo | **`StatusBadge`** con su tono (neutral, info, progress, success, warning, danger), como en el Portal; `StatusDot` en filas | `Badge` para estados: `Badge` es para categorías |
| Partes de un total o un ranking | `BarList` (con `display` para el valor formateado) | `Chart` `pie` con muchas porciones |
| Evolución en el tiempo | `Chart` `line`, `area` o `bar` | `Table` |
| Detalle tabular | `Table`, con `caption` que diga el corte o el top N | |
| Datos clave de una ficha | `KeyValue` (1–3 columnas) | |
| Un proceso por etapas | **`Stages`** (done, current, upcoming) | `Timeline`, que es para fechas y eventos |
| Requisitos o entregables con estado | **`Checklist`** | `List` |
| Hitos con fecha | `Timeline` | |
| Una lista de archivos, personas o integraciones | `Item` apilados en un `Stack` `gap: "sm"` | `List` |
| Secciones de un proyecto como en el Portal | `UnderlinedTabs` | `Tabs` |
| Una conclusión o un riesgo | `Alert` (uno; el que hay que atender) | Varios `Alert` |

**Controles y estados son de mockup:**
- Button, ButtonGroup, ActionMenu, FilterBar, ToggleGroup, Input, Select, Textarea, Checkbox, RadioGroup, Switch, Calendar, Command, Dropzone, Pagination y Breadcrumb **no hacen nada**: son decorativos. Un `Button` o un `Link` con `href` solo navega.
- EmptyState, ErrorState, LoadingState, Skeleton, Spinner, MilestoneGanttLegend y MilestoneGanttSkeleton dibujan los estados de una pantalla.

Úsalos para **mockups de pantallas**, no en un dashboard de datos reales: ahí darían a entender que se puede filtrar o actuar.

## Recetas

Cada receta tiene un ejemplo completo y validado en `${CLAUDE_PLUGIN_ROOT}/skills/views/examples/`. Parte de él.

1. **Resumen en la conversación** (`render-payments-summary.json`, `view_render`): `Section` con origen y corte → `Grid` de `Metric` → `BarList` → `Item` con lo siguiente.
2. **Tablero de KPIs** (`kpi-dashboard.json`): `Section` con `StatusBadge` de salud y un `Alert` → `Grid` de 4 `Metric` → `UnderlinedTabs` con `Stages` + `Table` y `Chart` + `BarList`.
3. **Mockup de pantalla** (`app-screen.json`): `AppShell` (brand, `nav` con uno `active`, `title`, `user`) → `Breadcrumb` → KPIs → `Alert` → `Card` con `action` y `menu`, que contiene `FilterBar` + `Table` + `Pagination`.
   - Se ve en un marco de escritorio, tableta o móvil y se abre a pantalla completa.
   - Para los estados vacíos o de error de la pantalla, haz variantes con `EmptyState` o `ErrorState`.
   - Liga el mockup desde el nodo `screen` (skill `screens`) con `wireframe: {description, pageId}`.
4. **Reporte visual o ficha** (`visual-report.json`): `Heading` h1 + `Text` lead → `Stages` → `KeyValue` → `Progress` → `Checklist` de entregables → `Timeline` → `Accordion`.
5. **Comparativo** (`comparison.json`): `Section` → `Grid` de `Card`, una por opción, con `StatusBadge` (Recomendada, Alternativa o Descartada), `KeyValue` y `List` → `Alert` `info` con la conclusión. No anides `Card` dentro de `Card`.

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
   - `audience`: `equipo` o `cliente`;
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
