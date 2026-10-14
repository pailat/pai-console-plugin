# Tipos de page y bloques

> Generado por `tools/gen-references.ts` desde pai-portal `04278b49d` (2026-10-14 Merge feat/0.2.5/resources-assets (ATE-229 parte A: assets del proyecto, modelo, API y serving)), `packages/contracts/src/pages`. No editar a mano: regenerar.

## Límites del contenido

- sections: 40
- blocks: 200
- text: 100000
- characters: 500000
- entities: 80
- relationships: 150
- facts: 24
- requirements: 60
- sources: 60
- risks: 40
- deliverables: 40
- tableColumns: 8
- tableRows: 200
- htmlBytes: 524288
- htmlTotalBytes: 1048576

## Reglas del catálogo

- IDs únicos en toda la page.
- Texto en Markdown; HTML literal, sin ejecutar JS.
- Mapas: expresa una pregunta, proposiciones, evidencia y límites; no dupliques la prosa.
- Cuestionarios: evalúa distinciones enseñadas; el resultado orienta repaso, no certifica.
- Las respuestas del lector no forman parte del documento.
- Imágenes privadas: crea primero la page, sube sus archivos y conserva sólo /api/pages/assets/{assetId}; el servicio valida pertenencia al documento.
- HTML interactivo: para un mockup o prototipo HTML (canvas, simulación, maqueta con JS) usa un bloque html {id, type: html, title, description?, html, height}; el Portal lo dibuja como un artifact de Claude, en un iframe aislado sin cookies, storage ni red. html es el documento completo o un fragmento, de hasta 512 KB (1 MB entre todos los de la page); height es auto o px entre 120 y 4000. Scripts sólo inline o de html.scriptSources; sin fetch ni XHR (connect-src 'none'): los datos van dentro del HTML. Usa las variables de tokens de Pai (--background, --foreground, --border, --primary…) para verse en claro y oscuro. Un ```html preview nunca va en el Markdown.
- Pizarras: para mostrar en la page una pizarra del proyecto usa un bloque whiteboard {id, type: whiteboard, page, title?}; page es el id de una page de formato whiteboard del mismo proyecto (créala con whiteboard_create). Se dibuja su vista previa con «Abrir» y, para quien puede editarla, «Editar aquí». Una page para el cliente sólo embebe pizarras visibles para el cliente.
- Embeds: el bloque embed guarda sólo un enlace https (Figma, Google Slides, Miro, YouTube, Loom o cualquier sitio); nunca HTML ni código <iframe>.
- Figuras: usa el bloque figure con assetId null mientras no exista el archivo; nunca inventes un assetId ni enlaces una imagen externa.
- Fuentes: declara cada fuente una vez en un bloque sources con enlace y fecha ISO; facts, data-table, quote y figure la citan por sourceRef.
- Datos: una cifra vive en facts o data-table con su fecha de corte; no repitas la misma cifra en prosa sin su fuente.
- Requisitos y entregables: el entregable referencia requisitos por id; un requisito sin criterio de aceptación no es un requisito.
- Vistas: para un tablero, reporte visual o página libre usa un bloque view (ocupa el ancho que necesita; no hace falta layout); compón su spec sólo con los componentes de views.groups (layout, métricas, gráficas, tablas) y valídalo con page_validate antes de guardar. Ningún tipo built-in admite el bloque view: una page con vista va sin typeSlug, o con un tipo propio de la organización o del proyecto cuyas secciones lo permitan.
- Conocimiento (schemaVersion 2): un bloque cita nodos del proyecto o de su organización con refs [{nodeId, revision, role}] (role cites, grounds o subject), o en línea con [texto](kb:kind/slug@rN) en text, callout, cards y comparison; al guardar, el servidor agrega cada cita en línea a refs del bloque (sin @rN toma la revisión vigente). Una page para el cliente (audience client) sólo cita nodos visibles para el cliente: page_validate los lista.
- Proyecciones (schemaVersion 2): para mostrar en la page lo que ya vive en Conocimiento (diagrama C4 o ERD, pantallas, casos de uso, flujos, listas de decisiones, requisitos, riesgos, glosario…) usa un bloque projection {id, type: projection, format, selection, params?, title?, caption?} en vez de copiar los datos: no guarda datos propios, se dibuja al leer con lo que el lector puede ver. format es uno de projection.formats; selection es {refs: [{nodeId, revision}]} o {query: KnowledgeQuery} (la misma de knowledge_query), según lo que acepte el formato; los kinds deben ser los del formato y params cumple su esquema. caption es una línea de Markdown sin citas kb:. Valida con page_validate antes de guardar; una page para el cliente sólo proyecta nodos visibles para el cliente.

## Bloques

- `text`: Markdown con títulos, listas, tablas, enlaces y código literal.
- `callout`: Contexto, advertencia o conclusión con texto Markdown.
- `steps`: Secuencia de acciones con título y descripción.
- `cards`: Conceptos en dos, tres o cuatro columnas.
- `comparison`: Alternativas con texto Markdown.
- `timeline`: Fechas, eventos y su significado.
- `glossary`: Términos y definiciones desplegables.
- `mermaid`: Mermaid acotado, con alternativa textual y sin callbacks.
- `relationships`: Entidades posicionadas y conexiones con evidencia; exploración y lista accesible.
- `quiz`: Preguntas, opciones, respuestas correctas, explicación y enlace de repaso.
- `facts`: Cifras y métricas con unidad, fecha de corte, tendencia y fuente citada.
- `requirements`: Enunciado, prioridad, justificación y criterio de aceptación por requisito.
- `sources`: Catálogo citable: título, enlace, tipo, editor y fecha de consulta.
- `figure`: Imagen privada del documento con texto alternativo, pie y crédito.
- `embed`: Iframe de Figma, Google Slides, Miro, YouTube, Loom o cualquier enlace https, con título y pie.
- `data-table`: Columnas declaradas y filas posicionales, con nota y fuente citada.
- `quote`: Voz textual con atribución, rol, contexto y fuente citada.
- `risks`: Riesgo con probabilidad, impacto, mitigación, responsable y estado.
- `deliverables`: Entregable con criterio de aceptación, responsable, fecha y requisitos.
- `view`: Vista libre compuesta con el catálogo pai-view@1 (layout, métricas, gráficas, tablas, pestañas). Su spec se describe en views.
- `html`: Mockup HTML con JS que se dibuja como un artifact de Claude, en un iframe aislado con pantalla completa.
- `whiteboard`: Una pizarra del proyecto, por su id: su vista previa con «Abrir» y, para quien puede editarla, «Editar aquí».

## Tipos built-in

Ninguno admite el bloque `view`: una page con vista se crea sin `typeSlug` (o con un tipo de la organización o del proyecto que lo permita). Los tipos de la organización o del proyecto se listan con `page_types`.

### `note` — Nota (v1)

Una idea y su contexto en una sola sección corta, para dejar constancia rápida.

Constraints: minSources 0, maxBlocksPerSection 4.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `nota` Nota | sí | text, callout | 1 |

### `guide` — Guía práctica (v1)

Enseña a hacer algo: contexto, pasos verificables, referencias con fecha y un cuestionario opcional.

Constraints: minSources 1, maxBlocksPerSection 8, bloques obligatorios: steps.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `contexto` Contexto | sí | text, callout | 1 |
| `pasos` Cómo hacerlo | sí | steps, text, callout | 1 |
| `referencias` Referencias y límites | sí | text | 1 |
| `evaluacion` Comprueba lo aprendido | no | quiz | 1 |

### `decision` — Decisión (v1)

Registra una decisión: contexto, alternativas con ventajas y límites, la decisión, sus consecuencias y las fuentes.

Constraints: minSources 2, maxBlocksPerSection 8, bloques obligatorios: comparison.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `contexto` Contexto | sí | text, callout | 1 |
| `alternativas` Alternativas | sí | comparison, cards, text | 1 |
| `decision` Decisión | sí | callout, text | 1 |
| `consecuencias` Consecuencias | sí | text, cards, steps | 1 |
| `fuentes` Fuentes | sí | text | 1 |

### `report` — Reporte (v1)

Informa un resultado: resumen ejecutivo, hallazgos, evidencia que los respalda, recomendaciones y fuentes.

Constraints: minSources 2, maxBlocksPerSection 10, bloques obligatorios: steps.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `resumen` Resumen ejecutivo | sí | callout, text | 1 |
| `hallazgos` Hallazgos | sí | cards, text, comparison | 1 |
| `evidencia` Evidencia | sí | text, timeline, comparison, mermaid | 1 |
| `recomendaciones` Recomendaciones | sí | steps, text | 1 |
| `fuentes` Fuentes | sí | text | 1 |

### `process` — Proceso (v1)

Documenta un proceso operativo: objetivo, actores, pasos con diagrama, excepciones y cuestionario final.

Constraints: minSources 0, maxBlocksPerSection 8, quiz tras cada sección, bloques obligatorios: mermaid, steps, quiz.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `objetivo` Objetivo | sí | text, callout | 1 |
| `actores` Actores | sí | cards, glossary, text | 1 |
| `pasos` Pasos | sí | steps, mermaid, text | 2 |
| `excepciones` Excepciones | sí | text, callout, cards | 1 |
| `evaluacion` Comprueba lo aprendido | sí | quiz | 1 |

### `project-overview` — Resumen de proyecto (v1)

Presenta un proyecto completo en una página: propósito, objetivos, alcance, métricas con fuente y riesgos abiertos.

Constraints: minSources 1, maxBlocksPerSection 8, bloques obligatorios: facts, risks, sources.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `resumen` Resumen | sí | callout, text, facts | 1 |
| `objetivos` Objetivos | sí | cards, text | 1 |
| `alcance` Alcance | sí | deliverables, text, cards | 1 |
| `metricas` Métricas | sí | facts, data-table, text | 1 |
| `riesgos` Riesgos | sí | risks, text | 1 |
| `fuentes` Fuentes | sí | sources | 1 |

### `prd` — Requisitos de producto (v1)

Define qué debe construirse: contexto, usuarios, requisitos con criterio de aceptación, alcance, métricas de éxito y fuentes.

Constraints: minSources 1, maxBlocksPerSection 10, bloques obligatorios: requirements, facts, sources.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `contexto` Contexto | sí | text, callout, quote | 1 |
| `usuarios` Usuarios | sí | cards, quote, text | 1 |
| `requisitos` Requisitos | sí | requirements, text | 1 |
| `alcance` Alcance | sí | deliverables, comparison, text | 1 |
| `metricas` Métricas de éxito | sí | facts, data-table, text | 1 |
| `riesgos` Riesgos | no | risks, text | 1 |
| `fuentes` Fuentes | sí | sources | 1 |

### `sow` — Propuesta de trabajo (v1)

Acuerda un trabajo: contexto, entregables con aceptación, exclusiones explícitas, plan, inversión y supuestos.

Constraints: minSources 1, maxBlocksPerSection 8, bloques obligatorios: deliverables, data-table, sources.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `contexto` Contexto | sí | text, callout | 1 |
| `alcance` Alcance | sí | deliverables, text | 1 |
| `fuera-de-alcance` Fuera de alcance | sí | text, cards | 1 |
| `plan` Plan | sí | timeline, steps, text | 1 |
| `inversion` Inversión | sí | data-table, facts, text | 1 |
| `supuestos` Supuestos | sí | text, callout, risks | 1 |
| `fuentes` Fuentes | sí | sources | 1 |

### `architecture` — Arquitectura (v1)

Describe cómo está construido un sistema: contexto, componentes, flujos con diagrama, restricciones y decisiones vigentes.

Constraints: minSources 1, maxBlocksPerSection 8, bloques obligatorios: mermaid, requirements, sources.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `contexto` Contexto | sí | text, callout, facts | 1 |
| `componentes` Componentes | sí | cards, relationships, text | 1 |
| `flujos` Flujos | sí | mermaid, steps, text | 2 |
| `restricciones` Restricciones | sí | requirements, text, risks | 1 |
| `decisiones` Decisiones vigentes | sí | text, comparison, callout | 1 |
| `fuentes` Fuentes | sí | sources | 1 |

### `discovery-report` — Reporte de descubrimiento (v1)

Cierra una fase de descubrimiento: objetivo, método, hallazgos con cifras, evidencia textual, riesgos y recomendaciones.

Constraints: minSources 2, maxBlocksPerSection 8, bloques obligatorios: facts, quote, sources.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `objetivo` Objetivo | sí | text, callout | 1 |
| `metodo` Método | sí | steps, text | 1 |
| `hallazgos` Hallazgos | sí | facts, cards, text | 1 |
| `evidencia` Evidencia | sí | quote, data-table, figure, text | 1 |
| `riesgos` Riesgos | sí | risks, text | 1 |
| `recomendaciones` Recomendaciones | sí | steps, deliverables, text | 1 |
| `fuentes` Fuentes | sí | sources | 1 |

### `design-inventory` — Inventario de diseño (v3)

Levanta lo que existe en la interfaz: alcance del corte, inventario de pantallas y componentes, piezas, brechas y siguientes pasos.

Constraints: minSources 1, maxBlocksPerSection 12, bloques obligatorios: data-table, sources.

| sección | obligatoria | bloques permitidos | mín. |
|---|---|---|---|
| `alcance` Alcance del inventario | sí | text, callout | 1 |
| `inventario` Inventario | sí | data-table, cards, text | 1 |
| `piezas` Piezas | sí | figure, embed, cards, text | 1 |
| `brechas` Brechas | sí | risks, requirements, text | 1 |
| `siguientes-pasos` Siguientes pasos | sí | steps, deliverables, text | 1 |
| `fuentes` Fuentes | sí | sources | 1 |
