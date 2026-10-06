---
name: views
description: Compone vistas de Pai (catálogo pai-view@1) en Recursos de Pai Console. Cubre tableros y dashboards con KPIs, mockups de pantallas de aplicación con AppShell, reportes visuales, fichas, comparativos y estados de proyecto, como un bloque view en una page canvas. Úsalo cuando pidan un tablero, dashboard, vista, mockup, wireframe, pantalla de una app, reporte visual, KPIs o gráficas en Pai, o editar una vista existente.
argument-hint: "[proyecto] [qué vista: tablero, pantalla, reporte…]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Vistas de Pai (`pai-view@1`)

Lee antes el skill `pai-console`: entorno, descubrimiento, buscar antes de crear, CAS. La page que contiene la vista se crea con el método del skill `resources`; aquí está cómo componer la vista.

**Catálogo completo**, generado desde el código: `${CLAUDE_PLUGIN_ROOT}/skills/views/references/view-catalog.md`. Tiene los componentes, sus props con tipos y límites, y las reglas.

## Vista o page de documento

| Usa una **vista** cuando… | Usa una **page de documento** (bloques `facts`, `data-table`, `timeline`, `cards`) cuando… |
|---|---|
| El acomodo importa: KPIs en rejilla, pestañas, gráfica junto a tabla | Se lee de corrido: explicación, decisión, guía |
| Es un tablero, un mockup de pantalla o una ficha visual | Cada cifra necesita su **fuente citada** (`sourceRef`) |
| Es un vistazo con fecha de corte | Debe cumplir un tipo (`report`, `prd`, `sow`…) |

**Una vista no cita fuentes ni consulta datos en vivo:** es una foto con fecha de corte. Si cada cifra debe ir citada, usa `facts` o `data-table` en una page tipada, y como mucho una vista de resumen aparte.

## Dónde vive

- Una vista es un **bloque `view` en una page con `layout: "canvas"`**: `{ "id", "type": "view", "title", "spec": { "root": "<id>", "elements": { … } } }`.
- **Sin `typeSlug`:** ningún tipo built-in admite `view` (`page_validate` da `bloque-no-permitido`). Solo un tipo de la organización o del proyecto que lo permita, si `page_types` lo lista.
- Una page canvas puede tener varias secciones con su vista cada una (por ejemplo «Resumen» y «Detalle»). Lo normal es una sola vista por page.
- **Ruta en inglés**, por carpeta: `dashboards/<tema>`, `mockups/<módulo>`, `reports/<tema>`.

## El spec

```json
{ "root": "root",
  "elements": {
    "root": { "type": "Stack", "props": { "direction": "vertical", "gap": "lg" }, "children": ["header", "kpis"] },
    "header": { "type": "Section", "props": { "title": "…", "description": "Corte al 2026-10-06" } },
    "kpis": { "type": "Grid", "props": { "columns": 3, "gap": "md" }, "children": ["k1", "k2", "k3"] },
    "k1": { "type": "Metric", "props": { "label": "…", "value": "68 %" } }
  } }
```

- **Plano:** cada elemento se declara una vez en `elements` y se referencia por id en `children`. Tiene **un solo padre**, todo cuelga de `root` y no hay ciclos ni elementos sueltos.
- **Ids** en inglés, camelCase, que digan qué son (`kpiRevenue`, `loansChart`, no `e7`). Son únicos y empiezan con letra. **Al editar, conserva los ids** de lo que no cambia.
- Solo admiten `children` **AppShell, Stack, Grid, Card, Collapsible, Tabs y Section**. **Tabs** lleva un hijo por pestaña, en el orden de `props.tabs`; normalmente cada hijo es un Stack.
- Props estrictas: **solo** las del catálogo. Nunca `className`, `style`, colores, HTML, `$state`, `$cond`, `visible`, `on` ni `repeat`.
- Las props que admiten `null` se pueden omitir. Las demás son obligatorias, por ejemplo `title` de Chart y `value` de Metric.

## Recetas

Cada receta tiene un ejemplo completo y validado en `${CLAUDE_PLUGIN_ROOT}/skills/views/examples/`. Parte de él y cambia los datos.

### 1. Tablero de KPIs (`kpi-dashboard.json`)

`Stack` → `Section` (título y corte) con un `Alert` si hay algo que atender → `Grid` de 3–4 `Metric` → `Tabs` con `Chart` y `Table`.

- 3 o 4 métricas por fila. Si hay más, agrúpalas en dos `Grid` con su `Heading` h3.
- **Un solo `Alert`**: lo único que hay que atender. Si todo va bien, no pongas ninguno.
- `trend` solo cuando hay comparación real, y entonces di contra qué en `detail` («vs. agosto»).

### 2. Pantalla de aplicación / mockup (`app-screen.json`)

Raíz **`AppShell`** con:
- `brand` (el producto);
- `nav` (≤12, con iconos del catálogo, uno `active: true`);
- `title` (la pantalla);
- `user`;
- su contenido en un `Stack`.

En Recursos se ve en un marco de escritorio, tableta o móvil y se abre a pantalla completa.

- Úsalo para wireframes de pantallas. Después liga la page desde el nodo `screen` (skill `screens`) con `properties.wireframe: { description, pageId }`.
- Iconos permitidos: dashboard, chart, file, folder, users, user, building, home, calendar, wallet, receipt, commission, reports, settings, help, search, bell, mail, map, layers, briefcase, key.
- Usa datos verosímiles del dominio del cliente, no «Lorem ipsum». Marca que es un mockup en el `title` del bloque view («Mockup — Préstamos»).

### 3. Reporte visual o ficha (`visual-report.json`)

`Stack` → `Heading` h1 + `Text` lead → `KeyValue` (datos clave en 2–3 columnas) → `Progress` → `Timeline` (hitos con `status` done/current/upcoming) → `Accordion` o `Collapsible` para el detalle secundario.

### 4. Comparativo (`comparison.json`)

`Section` → `Grid` de 2–3 `Card`, una por opción, cada una con `KeyValue` y `List` (pros y contras) y un `Badge` para la recomendada → `Alert` `info` con la conclusión.

- No anides `Card` dentro de `Card`.
- Si la decisión importa, regístrala además como nodo `decision` (skill `knowledge`).

## Datos

- **Valores ya formateados**, en español de México: `"1 240"`, `"$412,300 MXN"`, `"68 %"`, `"3.4 s"`. `Metric.value` admite como máximo 40 caracteres.
- **Fecha de corte siempre**, en la `description` de la `Section`, en el `detail` de una `Metric` o en el `caption` de una `Table`.
- Si los datos vienen del MCP (`timeline_get`, `payment_list`, `product_get`…), di de qué tool y con qué fecha. La vista no se actualiza sola: para refrescarla, vuelve a leer y haz `page_update`.
- **Chart:**
  - cada serie trae **un valor por categoría**, en el mismo orden;
  - `pie` lleva una sola serie;
  - como máximo 6 series y 60 categorías;
  - `unit` corto (`"h"`, `"MXN"`, `"%"`);
  - `stacked` solo para partes de un total.
- **Table:** ≤10 columnas y ≤200 filas, con cada fila del mismo largo que `columns`. Para rankings, muestra el top N y dilo en `caption`.
- Textos ≤2000 caracteres, etiquetas ≤160. Una vista tiene ≤300 elementos y ≤12 niveles.
- `Link.href`: solo rutas del Portal (`/organization/projects/…`), `#ancla`, `https:` o `mailto:`.

## Diseño

- **Jerarquía clara:** un título principal (`Section` o `Heading` h1) y debajo bloques del mismo nivel. `Grid` para lo paralelo, `Stack` para lo secuencial, `Tabs` para vistas alternativas del mismo dato (no para pasos).
- **Menos es más:** cada elemento responde una pregunta. No pongas una gráfica y una tabla con los mismos números en la misma pestaña.
- **Estados con `Badge`** (`default`, `secondary`, `destructive`, `outline`). Conclusiones y riesgos con `Alert` (`info`, `success`, `warning`, `error`). No uses colores.
- Etiquetas en español y cortas. Sin jerga técnica en vistas para el cliente.

## Flujo

**Crear:**
1. Busca (`page_search`, `page_list`) si ya existe la vista. Si existe, edítala.
2. Elige la receta, copia su ejemplo y cambia los datos.
3. `page_validate {content}` sin `typeSlug`, hasta que no haya `issues`.
4. `page_create`: `layout: "canvas"`, `path` en inglés, `audience` (`equipo` o `cliente`), `summary` ≤80, `idempotencyKey` estable.

**Editar:**
1. `page_read {path, view: "full"}`: guarda `document.id` y `document.revision`.
2. Cambia el `spec` **sobre esa copia**, conservando los ids.
3. `page_validate` → `page_update` con `expectedDocumentId` y `expectedRevision`.

**Errores frecuentes de `page_validate`:**

| Mensaje | Causa |
|---|---|
| `Unrecognized key: "className"` | Prop fuera del catálogo |
| `Componente desconocido «X». Consulta el catálogo de vistas.` | Un `type` que no está en `pai-view@1` |
| `Too big: expected number to be <=4` | `Grid.columns` mayor que 4 |
| `El hijo «x» no existe.` | Un id de `children` que no está en `elements` |
| `«x» ya es hijo de «y»; cada elemento tiene un solo padre.` | El mismo id en dos `children` |
| `«x» no está conectado a la raíz; enlázalo como hijo o elimínalo.` | Un elemento suelto, que no cuelga de `root` |
| `Tabs declara N pestaña(s) y tiene M hijo(s): pon uno por pestaña.` | `props.tabs` y `children` de distinto largo |
| `La serie «S» tiene N valor(es) y hay M categoría(s).` | Una serie de `Chart` sin un valor por categoría |
| `bloque-no-permitido` | La page lleva `typeSlug`: quítalo |

## El catálogo crece

El catálogo `pai-view@1` es la fuente de verdad, y en pai-portal se está ampliando con más componentes de Pai.

- La referencia de este plugin se regenera desde el código (`tools/gen-references.ts`).
- Si el servidor ofrece un componente que la referencia no tiene, **manda el servidor**. Consúltalo en `page_catalog` → `views.components`; delega esa lectura al agente `pai-explorer` para no cargar el catálogo entero.
- **Nunca inventes componentes ni props:** si algo no está en el catálogo, compónlo con lo que hay o dilo.
