# Catálogo de vistas `pai-view@1`

> Generado por `tools/gen-references.ts` desde pai-portal `e4fef942` (2026-10-06 Merge pull request #137 from pailat/fix/0.2.5/erd-c4-ui-rules), `packages/views/src/catalog.ts`. No editar a mano: regenerar.

Formato: Spec plano de json-render: { root: id, elements: { [id]: { type, props, children? } } }. Los hijos se referencian por id.

## Reglas

- Usa sólo los componentes de este catálogo; no hay className, style, colores ni HTML.
- Los ids son únicos, empiezan con letra y se reutilizan al editar.
- Las props omitidas que aceptan null toman su valor por defecto.
- Sólo AppShell, Stack, Grid, Card, Collapsible, Tabs y Section tienen hijos; Tabs lleva un hijo por pestaña, en orden.
- Para una pantalla de aplicación (dashboard, módulo) usa AppShell como raíz: así la vista se ve con su barra lateral y se puede abrir a pantalla completa.
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
- gridColumns: 4
- navItems: 12

## Componentes

Las props que aceptan `null` son opcionales en la práctica: si se omiten toman su valor por defecto. Las demás son obligatorias.

### Stack (admite hijos)

Contenedor flex vertical u horizontal; la base de cualquier vista. Sus hijos se apilan con el espacio indicado.

- `direction`: "horizontal"|"vertical" (null = por defecto)
- `gap`: "none"|"sm"|"md"|"lg"|"xl" (null = por defecto)
- `align`: "start"|"center"|"end"|"stretch" (null = por defecto)
- `justify`: "start"|"center"|"end"|"between"|"around" (null = por defecto)

### Grid (admite hijos)

Cuadrícula de 1 a 4 columnas que se apila en móvil. Úsala para tarjetas de métricas o grupos paralelos.

- `columns`: integer (≥1, ≤4) (null = por defecto)
- `gap`: "sm"|"md"|"lg"|"xl" (null = por defecto)

### Card (admite hijos)

Tarjeta con título y descripción opcionales que agrupa contenido relacionado. No la uses como encabezado de la vista ni anides tarjetas dentro de tarjetas.

- `title`: string (null = por defecto)
- `description`: string (null = por defecto)
- `maxWidth`: "sm"|"md"|"lg"|"full" (null = por defecto)
- `centered`: boolean (null = por defecto)

### Separator

Línea divisoria entre bloques.

- `orientation`: "horizontal"|"vertical" (null = por defecto)

### Tabs (admite hijos)

Pestañas. Declara las pestañas en tabs y pon un hijo por pestaña, en el mismo orden (normalmente un Stack).

- `tabs`: [{ label: string (min 1, ≤160), value: string (min 1, ≤80) }] (min 2, máx 8)
- `defaultValue`: string (null = por defecto)

### Accordion

Secciones desplegables de texto (preguntas frecuentes, detalles secundarios).

- `items`: [{ title: string (min 1, ≤160), content: string (≤2000) }] (min 1, máx 60)
- `type`: "single"|"multiple" (null = por defecto)

### Collapsible (admite hijos)

Una sección desplegable con título; sus hijos se muestran al abrirla.

- `title`: string
- `defaultOpen`: boolean (null = por defecto)

### Heading

Título de una parte de la vista. h1 sólo para el título principal; luego h2 y h3.

- `text`: string
- `level`: "h1"|"h2"|"h3"|"h4" (null = por defecto)

### Text

Párrafo de texto plano (sin Markdown). Variantes: body, lead (introducción), muted, caption, code.

- `text`: string
- `variant`: "body"|"caption"|"muted"|"lead"|"code" (null = por defecto)

### Badge

Etiqueta corta de estado o categoría.

- `text`: string
- `variant`: "default"|"secondary"|"destructive"|"outline" (null = por defecto)

### Alert

Aviso destacado: info, success, warning o error. Úsalo para conclusiones, riesgos o advertencias.

- `title`: string
- `message`: string (null = por defecto)
- `type`: "info"|"success"|"warning"|"error" (null = por defecto)

### Table

Tabla de datos: columns son los encabezados y rows un arreglo de filas con una celda por columna.

- `columns`: [string (min 1, ≤160)] (min 1, máx 10)
- `rows`: [[string (≤640)]] (máx 200)
- `caption`: string (≤160) (null = por defecto)

### Progress

Barra de avance de 0 a 100 con etiqueta opcional.

- `value`: number
- `max`: number (null = por defecto)
- `label`: string (null = por defecto)

### Avatar

Iniciales de una persona (sin imagen externa).

- `name`: string
- `size`: "sm"|"md"|"lg" (null = por defecto)

### Link

Enlace a una ruta del Portal (/organization/projects/…) o a un sitio https.

- `label`: string (min 1, ≤160)
- `href`: string

### AppShell (admite hijos)

Simula una aplicación completa: barra lateral con marca, menú con iconos y usuario, y un encabezado con el título de la pantalla; sus hijos son el contenido. Úsalo como raíz de la vista. En Recursos se muestra en un marco con escritorio/tableta/móvil y se abre a pantalla completa; en pantallas angostas el menú pasa a un botón.

- `brand`: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) }
- `nav`: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key", active?: boolean (null = por defecto) }] (min 1, máx 12)
- `secondaryTitle`: string (≤80) (null = por defecto)
- `secondaryNav`: [{ label: string (min 1, ≤160), icon: "dashboard"|"chart"|"file"|"folder"|"users"|"user"|"building"|"home"|"calendar"|"wallet"|"receipt"|"commission"|"reports"|"settings"|"help"|"search"|"bell"|"mail"|"map"|"layers"|"briefcase"|"key", active?: boolean (null = por defecto) }] (máx 12) (null = por defecto)
- `title`: string (min 1, ≤160)
- `user`: { name: string (min 1, ≤160), detail?: string (≤80) (null = por defecto) } (null = por defecto)

### Section (admite hijos)

Región con título (h2) y descripción opcional que agrupa los bloques de un tema de la vista.

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)

### Metric

Indicador (KPI): etiqueta, valor ya formateado («68 %», «$1.2 M») y detalle opcional con su comparación o fecha de corte.

- `label`: string (min 1, ≤160)
- `value`: string (min 1, ≤40)
- `detail`: string (≤160) (null = por defecto)
- `trend`: "up"|"down"|"flat" (null = por defecto)

### Chart

Gráfica con los colores del tema: bar, line, area o pie. categories es el eje X (o las porciones de pie) y cada serie trae un valor por categoría. pie usa una sola serie.

- `title`: string (min 1, ≤160)
- `description`: string (≤2000) (null = por defecto)
- `kind`: "bar"|"line"|"area"|"pie"
- `categories`: [string (min 1, ≤80)] (min 1, máx 60)
- `series`: [{ name: string (min 1, ≤80), values: [number] }] (min 1, máx 6)
- `unit`: string (≤20) (null = por defecto)
- `stacked`: boolean (null = por defecto)

### KeyValue

Pares etiqueta–valor (fechas, responsables, montos) en 1 a 3 columnas.

- `items`: [{ label: string (min 1, ≤160), value: string (min 1, ≤400) }] (min 1, máx 60)
- `columns`: integer (≥1, ≤3) (null = por defecto)

### List

Lista de viñetas o numerada de texto plano.

- `items`: [string (min 1, ≤640)] (min 1, máx 60)
- `ordered`: boolean (null = por defecto)

### Timeline

Cronología de hitos o eventos con fecha, título, descripción y estado (done, current, upcoming).

- `items`: [{ date: string (min 1, ≤40), title: string (min 1, ≤160), description?: string (≤2000) (null = por defecto), status?: "done"|"current"|"upcoming" (null = por defecto) }] (min 1, máx 60)

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
