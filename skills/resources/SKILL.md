---
name: resources
description: "Crea y mantiene Recursos de un proyecto de Pai Console. Cubre pages (pai-page) con tipo y bloques, vistas con layout canvas y bloque view (catálogo pai-view@1), mockups y prototipos HTML (bloque html), pizarras (Excalidraw: whiteboard_* y bloque whiteboard), proyecciones de Conocimiento, atributos (fecha, responsable, estatus, etiquetas) y filtros, notas, carpetas, sugerencias, comentarios, imágenes y videos (assets: asset_list, asset_upload, asset_confirm, asset_delete; bloques figure y video) y archivos. Úsalo cuando pidan una page, documento, nota, carpeta, reporte, guía, PRD, SOW, arquitectura, tablero, dashboard, vista, mockup o prototipo HTML, pizarra, whiteboard, diagrama editable, lluvia de ideas o un diagrama desde Mermaid, marcar una page como aprobada o asignarle responsable, filtrar pages por estatus, responsable o etiqueta, sugerir cambios, comentar, subir imágenes, videos o documentos, reutilizar o borrar un asset, o mover, restaurar o borrar una page o una carpeta vacía."
argument-hint: "[proyecto] [tema o tipo de recurso]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Recursos en Pai: pages, vistas, pizarras, imágenes y archivos

Lee antes el skill `pai-console`.

**Referencias, generadas desde los contratos:**
- `references/page-types.md`: tipos built-in con sus secciones y bloques permitidos, límites y reglas;
- para componer vistas (`pai-view@1`), el skill **`views`**, con su catálogo y sus recetas.

Úsalas en lugar de `page_catalog`, que pesa unos 35 KB. Llama a `page_catalog` o a `page_types` solo si sospechas que el entorno tiene otra versión, o para ver los tipos propios de la organización o del proyecto.

## 1. Decide qué recurso es

| Necesitas… | Recurso |
|---|---|
| Un documento con estructura conocida (nota, guía, decisión, reporte, proceso, overview, PRD, SOW, arquitectura, discovery, inventario de diseño) | Page `layout: "document"` **con `typeSlug`** del tipo built-in. Sus secciones obligatorias mandan |
| Un tablero, reporte visual, mockup de pantalla o página libre con los componentes de Pai | Page `layout: "canvas"` con un bloque **`view`**, **sin `typeSlug`**: ningún tipo built-in admite `view` |
| Un mockup o prototipo con JavaScript libre (canvas, simulación, maqueta interactiva o pixel a pixel) | Page con un bloque **`html`** (§3), **sin `typeSlug`**: ningún tipo built-in lo admite. **No sirve como prototipo de una pantalla:** ese es siempre un bloque `view` (skill `screens`) |
| Un diagrama que el equipo o el cliente van a seguir editando a mano (lluvia de ideas, flujo, mapa, arquitectura en borrador), o un flowchart de Mermaid | **Pizarra** (`whiteboard_create`, §3): Excalidraw colaborativo en Recursos; se muestra en una page con un bloque `whiteboard`. Si solo se ve y no se edita, una vista `Flow` (skill `views`) |
| Mostrar en una page lo que ya vive en Conocimiento (C4, ERD, pantallas, flujos, decisiones, riesgos, glosario…) | Bloque **`projection`** en una page v2 (§3): se dibuja al leer, no copia datos |
| Una nota rápida en Markdown, que el cliente también puede escribir | Nota (`note_create`, §8) |
| Un archivo binario (PDF, hoja de cálculo, contrato) | Archivo de Recursos (§6), no una page |
| Conocimiento atómico (decisión, regla, entidad, componente) | Un nodo de Knowledge (skill `knowledge`), no una page |

Si dudas entre page y nodo, piensa en el uso. **Una page se lee de corrido; un nodo se consulta, se enlaza y se reemplaza.** Una page puede citar nodos y un nodo puede citar una page (`sources: [{type:"page", pageId}]`).

## 2. Crear una page

1. **Busca:** `page_search` con el tema y `page_list` (sigue `nextCursor`) para ver la estructura de rutas. Si existe una page para lo mismo, actualízala (§4).
2. **Elige el tipo:** `references/page-types.md`, o `page_types {slug}` para el `authoringGuide` completo y su ejemplo.
3. **Elige la ruta**, en inglés, kebab-case y por carpetas: `architecture/payments`, `reports/checkout-performance`, `dashboards/project-status`, `guides/deploy-staging`. Sin extensión y sin fechas en la ruta, salvo en las series (`reports/2026-10-weekly`).
4. **Compón el contenido:**
   ```json
   { "schemaVersion": 1, "componentSetVersion": "pai-core-v1", "layout": "document",
     "sections": [ { "id": "resumen", "title": "Resumen", "blocks": [ { "id": "intro", "type": "text", "markdown": "…" } ] } ] }
   ```
   - Los ids de sección son los del tipo (por ejemplo `resumen`, `hallazgos`), en el orden del tipo.
   - Los ids de bloque siguen `^[a-zA-Z][a-zA-Z0-9_-]{0,79}$` y son únicos en toda la page. Usa nombres que digan qué es (`summaryCallout`, no `b1`).
   - Límites: 40 secciones, 200 bloques y 500 000 caracteres de JSON.
5. **`page_validate {content, typeSlug}`** hasta que no haya `issues`. Además del contrato, revisa la estructura (secciones faltantes o desordenadas, bloques no permitidos) y la calidad (fuentes con URL y fecha, texto mínimo).
6. **`page_create`** con:
   - `path`, `title` (en español), `description`, `typeSlug`;
   - `audience`: `internal` (solo el equipo) o `client` (la ve el cliente). Si no te lo dijeron, pregunta; si nadie decide, usa `internal`;
   - `content`, `summary` (≤80, como un mensaje de commit);
   - `idempotencyKey`: `page-<proyecto>-<ruta-con-guiones>`.
7. **Lee la respuesta** (`warnings`, `document.revision`) y da a la persona:
   - la ruta y la revisión;
   - el enlace del Portal: el `url` de la respuesta con el host del Portal delante (`https://app.pai.lat` en producción; en staging, el Portal de staging).

Ejemplos validados:
- `examples/report-page.json`: tipo `report`, con sus cinco secciones obligatorias;
- vistas en canvas: ejemplos en `../views/examples/`.

## 3. Vistas, HTML, proyecciones y pizarras

**Elige el bloque:** datos o un tablero con los componentes de Pai → `view`; interacción con JavaScript libre o una maqueta pixel a pixel → `html`; datos vivos de Conocimiento → `projection`; un enlace a Figma, Slides, Miro, YouTube o Loom → `embed` (solo la URL https, nunca HTML ni `<iframe>`).

### `view` (catálogo `pai-view@1`)

Tableros, mockups de pantallas, reportes visuales y comparativos se componen con el skill **`views`**: catálogo, recetas validadas, reglas de datos y diseño, y errores frecuentes. Aquí solo lo esencial de la page que la contiene:
- `layout: "canvas"` y un bloque `{id, type: "view", title, spec}`;
- **sin `typeSlug`**;
- valida con `page_validate` antes de guardar.

### `html` (mockups y prototipos interactivos)

El Portal lo pinta como un artifact de Claude: un iframe aislado (`sandbox="allow-scripts"`, sin cookies, storage, popups, formularios ni red).

```json
{ "id": "flowMockup", "type": "html", "title": "Mockup del flujo", "description": "Elige un paso para ver su detalle.", "height": "auto",
  "html": "<style>body{margin:0;padding:16px;background:var(--background);color:var(--foreground)}button{border:1px solid var(--border);border-radius:8px;background:var(--card);color:inherit}</style><button id=b>Aprobar</button><p id=d></p><script>b.onclick=()=>d.textContent='Aprobado';</script>" }
```

- **Campos:** `title` (1-240, es el nombre accesible y el título en el índice), `description?` (≤240), `html` (documento completo o fragmento), `height`: `"auto"` (crece con el contenido hasta 4000) o un entero en px de **120 a 4000**.
- **Topes:** **512 KB por bloque** y **1 MB entre todos los bloques html de la page**, en bytes UTF-8. Cada versión guarda el contenido entero.
- **Scripts:** inline, o con `src` https solo desde `https://cdnjs.cloudflare.com/`, `https://cdn.jsdelivr.net/npm/`, `https://unpkg.com/` y `https://cdn.tailwindcss.com/`. Estilos inline o de `fonts.googleapis.com`; fuentes de `fonts.gstatic.com`. Imágenes `data:`, `blob:` o https.
- **Sin red:** la CSP lleva `connect-src 'none'`: `fetch`, XHR, WebSocket, EventSource y `sendBeacon` fallan. **Pon los datos dentro del HTML.**
- **Tema:** el Portal inyecta los tokens de Pai y del tema de la organización como variables CSS y los cambia en vivo con el tema. Usa `var(--background)`, `var(--foreground)`, `var(--card)`, `var(--muted)`, `var(--muted-foreground)`, `var(--border)`, `var(--primary)`, `var(--primary-foreground)`, `var(--success)`, `var(--warning)`, `var(--destructive)`, `var(--chart-1)`…`var(--chart-5)`, `var(--radius)`, `var(--font-sans)`: los mismos nombres sirven en claro y en oscuro. No fijes colores a mano.
- **Errores** (rechazan la escritura; en `page_create`/`page_update` llegan como `BAD_REQUEST` con `ruta: mensaje`, en `page_validate` en `issues`):
  - `HTML_BLOCK_TOO_LARGE` y `HTML_PAGE_TOO_LARGE`: recorta o parte en varias pages;
  - `HTML_SCRIPT_HOST`: un `src` fuera de la lista, sin https, relativo al protocolo (`//…`) o con usuario, contraseña o puerto. Cambia al CDN permitido o mete el script inline;
  - `HTML_PREVIEW_IN_MARKDOWN`: un fence ```` ```html preview ```` dentro del Markdown de un bloque; escríbelo como bloque `html`.
- **Avisos** (se guarda igual, en `warnings`, también en `page_validate`):
  - `html-network-blocked`: el HTML llama a la red y fallará. Corrígelo: mete los datos;
  - `html-sensitive-field`: pide contraseñas, tarjetas o códigos de un solo uso (`type=password`, `autocomplete=cc-*` o `one-time-code`). Que sea un mockup evidente; nunca pidas datos reales.
- **Citas:** un `kb:` dentro del `html` no es una cita ni se indexa. Para citar Conocimiento usa `refs` del bloque (v2), o cítalo en `title`/`description`.
- **Cliente:** en una page `audience: client` el cliente ve el bloque (sin el botón «Ver código», que es de staff) y `page_read` le da el `html` íntegro: no metas nada interno. En una page v2, todo `kb:` del html se le reemplaza por su texto.
- **Console no lo edita:** no crea el bloque ni cambia su HTML o altura (solo título y descripción). Lo crea y lo cambia el agente con `page_create`/`page_update`.
- `page_read view=content` y la búsqueda lo resumen como «HTML interactivo · ábrelo en el Portal», sin el código.
- Una nota Markdown con un fence ```` ```html preview h=400px ```` de primer nivel se convierte en bloque `html` al migrarla (`page_migrate`); dentro de una lista o una cita la conversión falla: sácalo a primer nivel.

### `projection` (Conocimiento vivo en una page)

En una page `schemaVersion: 2`, un bloque `{id, type: "projection", format, selection: {refs} | {query}, params?}` dibuja al leer lo que el lector puede ver: no guarda datos propios. Formatos: `c4`, `erd`, `screen`, `screen-list`, `use-case`, `use-case-list`, `flow`, `decision-table`, `requirement-list`, `risk-list`, `assumption-list`, `glossary`, `fact-list`, `actor-list`, `task-timeline`, `node-cards`, `knowledge-table`. Valida con `page_validate` y guarda con `page_update`.

Para **ver** uno ya guardado:
- `page_projection {path, blockId}` lo dibuja en el lienzo como el lector del Portal (el `blockId` sale de `page_read`). Devuelve `projection.state`: `ready`, `empty` (nada visible para quien lee) o `broken` (con `message`; staff ve además `missing`). También lo tiene el cliente, que solo ve pages y nodos para el cliente.
- `page_read view=full` trae las `projections` resueltas como datos, sin dibujo: úsala para razonar o editar.
- `knowledge_view` (staff) dibuja un ERD o C4 directo del grafo, sin page.
- Errores: un `blockId` que no existe es `NOT_FOUND`; un bloque que no es `projection` es `BAD_REQUEST` (léelo con `page_read`).

### Pizarras (`whiteboard_*` y bloque `whiteboard`)

Una pizarra es una page de formato `whiteboard`: una escena de Excalidraw en Recursos que se edita en vivo en el Portal (**Nuevo → Pizarra**). Sigue la regla de las notas: la crea el staff o un miembro de la organización cliente; la de un cliente la ve toda su organización y Pai y la edita su organización; la del staff nace `internal` salvo `audience: "client"`.

**Nunca escribes coordenadas.** Mandas `content` como `{graph}` o `{mermaid}` y el servidor acomoda y dibuja:
- `graph`: `{direction?: "TB"|"LR"|"RL"|"BT", nodes: [{id, label, shape?, group?, tone?}], edges?: [{from, to, label?, dashed?}], groups?: [{id, label}]}`. `shape`: `rectangle`, `ellipse`, `diamond`, `note` o `text`; `tone`: `default`, `info`, `success`, `warning`, `destructive` o `muted`. Ids con letras, números, `_ . : -`. Hasta 300 nodos, 600 aristas, 50 grupos y textos de 280 caracteres.
- `mermaid`: un `flowchart` (nodos `A[texto]`, `A(texto)`, `A([texto])`, `A{texto}`, `A((texto))`, `A>texto]`; aristas `-->`, `---`, `-.->`, `==>`, `-->|texto|`; `subgraph … end`), hasta 20 000 caracteres.

**Flujo:**
1. Crear: `whiteboard_create {path, title, content?, audience?, summary?, idempotencyKey?}`. `path` es la ruta completa (`diagramas/flujo-de-ventas`); sin `content` nace vacía. Devuelve `path`, `revision`, `url` y `summary` (lo que dice).
2. Leer: `whiteboard_read {path}` devuelve lo que dice (nodos con su id, texto, forma y grupo; conexiones; grupos; textos sueltos; `otherCount` cuenta trazos y formas que no son nodos), su `revision` y un boceto (`preview`). En hosts con MCP Apps se dibuja como vista `WhiteboardSketch`. Lee siempre antes de escribir: las personas dibujan a mano.
3. Escribir: `whiteboard_update {path, expectedRevision, mode, content, idempotencyKey, summary?, versionName?}`.
   - **`mode: "append"` por omisión:** agrega el contenido a la derecha de lo que hay; sus aristas pueden apuntar a nodos existentes por id o por texto, y los ids nuevos no pueden repetir los de la pizarra.
   - **`mode: "replace"` borra lo que dibujaron las personas:** úsalo solo si te lo piden explícitamente.
   - `idempotencyKey` es obligatoria: repítela solo para reintentar la misma escritura («La clave de idempotencia ya se usó con otro contenido» si cambias el contenido). `versionName` la nombra como «Guardar versión».
   - Quien tenga la pizarra abierta ve tu edición en vivo.
4. Errores: `CONFLICT` («La pizarra cambió desde que la leíste…»): relee con `whiteboard_read` e integra. `UNAVAILABLE` («la colaboración no está disponible»): reintenta con la misma clave. `page_update` o `note_update` sobre una pizarra dan «Esta página es una pizarra: se edita en el Portal o con whiteboard_update».
- `note_audience_set` (solo staff) la publica al cliente, y `page_move` la mueve sin perder la escena.
- `WhiteboardSketch` solo dibuja el `preview` que devuelve `whiteboard_read`: no lo inventes ni lo armes a mano.

**Mostrarla en una page:** un bloque `{id, type: "whiteboard", page, title?}`, donde `page` es el `document.id` (uuid) de la pizarra del mismo proyecto, no su ruta. Se dibuja su vista previa con «Abrir» y, para quien puede editarla, «Editar aquí». Ningún tipo built-in lo admite: va en una page sin `typeSlug`.
- `page_validate` da `WHITEBOARD_NOT_FOUND` (no existe en el proyecto) o `WHITEBOARD_NOT_A_BOARD` (no es pizarra), y avisa `WHITEBOARD_NOT_CLIENT_VISIBLE`: una page `client` no puede mostrar una pizarra solo del equipo.
- `page_read view=full` trae `whiteboards`: título y resumen de cada pizarra embebida, o `hidden` si no la ves.

### Flujos (bloque `flow`)

**Un flujo en una page:** bloque `{id, type: "flow", node, title?, height?}`. `node` es el uuid de un nodo `flow` del mismo proyecto y `height` los px del lienzo (240 a 1200; 480 por omisión). Se dibuja su lienzo en solo lectura con «Abrir». Los flujos se arman con el skill `flows`.

## 4. Actualizar una page

1. Si vas a reescribir, primero `page_comprehension` (staff ve el agregado; los demás, lo suyo): sus preguntas más falladas dicen qué explicar mejor. Es señal de práctica, nunca calificación de personas. `page_knowledge_health {path}` dice qué citas `kb:` quedaron reemplazadas, archivadas, contradichas o sin validar; sin `path`, cuenta por page.
   - `quiz_respond {path, blockId, answers | responses}` responde un cuestionario **en nombre de la persona**: cada intento cuenta y es suyo. Úsalo solo si ella te lo pide y con sus respuestas.
2. `page_read {path, view: "full"}`. Guarda `document.id` y `document.revision`.
3. Modifica **sobre ese contenido completo**. `page_update` **reemplaza** la page entera: nunca partas de `summary`, `content` parcial ni de `page_version`.
4. `page_validate` → `page_update {path, expectedDocumentId, expectedRevision, content, summary}`.
   - Para quitar el tipo: `detachType: true`. `typeSlug: null` no se acepta.
5. Ante `CONFLICT`: relee, integra y reintenta una vez.
6. Si `page_create` respondió con `replayed`, la page ya existía con esa clave: **relee** antes de actualizar, porque la revisión de la respuesta puede ser vieja.

## 5. Imágenes y videos (assets)

Las imágenes y los videos son **assets del proyecto**: se suben una vez y se usan por id en pages, notas y pizarras del mismo proyecto. Se ven en Recursos › Assets, con «Usado en». Nunca van como URL externa ni dataURL.

| Tool | Para |
|---|---|
| `asset_list {kind?, q?, cursor?, limit?}` | Buscar uno para reutilizarlo antes de subirlo otra vez: `kind` es `image`, `video` u `other` y `q` busca en el nombre; pagina con `nextCursor` (máx. 100). Trae `id`, nombre, tipo, tamaño, `href` y `usedIn`. En hosts con MCP Apps se dibuja como vista |
| `asset_get {assetId}` | Detalle: medidas o duración, quién lo subió, `href`, `usedIn` y `canDelete` |
| `asset_upload {filename, contentType, size, documentId?}` | Prepara la subida (no idempotente: cada llamada reserva un asset nuevo) |
| `asset_confirm {assetId}` | Confirma después del PUT; lo deja `ready` (idempotente) |
| `asset_delete {assetId}` | Lo borra para siempre (irreversible) |

Un cliente ve los assets que se usan en algo que ve, y los que subió y todavía no usa. `usedIn` solo lista lo que el lector ve.

### Subir: prepare → PUT → confirm

1. **Busca primero** con `asset_list` (por nombre y `kind`). Si ya existe, usa su `id`.
2. `asset_upload {organizationId, projectId, filename, contentType, size, documentId?}`.
   - Tipos y límites: PNG, JPEG, WebP y GIF hasta **10 MB**; SVG hasta **1 MB**; MP4 y WebM hasta **200 MB**. Si pasa del límite → `invalid_input` («El archivo pesa … bytes; el máximo para … es …»).
   - `size` son los bytes **exactos**: la URL firmada solo admite ese tamaño y ese `Content-Type`.
   - `documentId` (uuid, no ruta) es la page, nota o pizarra desde la que se sube, y tienes que poder editarla: si no, `FORBIDDEN` «Solo quien puede editar este documento sube archivos en él.». Sin `documentId` la subida va a la galería y **solo la hace el staff**; un cliente recibe «Solo el equipo de Pai sube assets desde la galería; súbelo desde tu nota o pizarra.».
   - Devuelve `assetId`, `signedUrl`, `method: "PUT"`, `headers`, `href` y `expiresIn` (300 s).
3. **PUT** de los bytes a `signedUrl` con exactamente los `headers` devueltos y antes de que caduque, por ejemplo `curl -X PUT --data-binary @fachada.png -H 'Content-Type: image/png' "<signedUrl>"`.
4. `asset_confirm {assetId}`. El servidor revisa lo que llegó:
   - que exista con el tamaño declarado (`ASSET_UPLOAD_MISSING`: vuelve a subirlo);
   - **sniff de bytes:** lee los primeros 64 KB y comprueba que el contenido sea del tipo declarado (`ASSET_CONTENT_MISMATCH`). Una extensión o un `contentType` falso no pasa;
   - **un SVG se lee completo, se sanea y se guarda saneado.** Si trae scripts o algo que el saneador no acepta, se rechaza con `ASSET_SVG_REFUSED`;
   - de las imágenes lee ancho y alto cuando el encabezado los trae.

   Si algo falla, responde `invalid_input` con su `reason`, borra el archivo y el asset queda `pending` e invisible. Empieza de nuevo con otro `asset_upload`. Confirmar un asset que ya está `ready` lo devuelve igual. Solo quien lo subió (o el staff) lo confirma.
5. Un asset `pending` que nadie confirma se barre a las 24 h. **Nunca guardes `signedUrl`:** se usa el `assetId` o el `href` (`/api/pages/assets/<assetId>`).

**`page_asset_upload {path, filename, contentType, size}`** sigue existiendo para imágenes PNG/JPEG/WebP/GIF ≤10 MB de una page ya creada. Es la misma subida con la page como origen, **sin `asset_confirm`**: el asset queda `pending` hasta que un `page_create` o `page_update` lo referencia, y esa escritura revisa sus bytes (si no son una imagen real, falla con el error del asset). Para videos, SVG, notas o pizarras usa `asset_upload`.

### Usarlo

Solo se aceptan assets del **mismo proyecto**, `ready` y que el autor vea. Uno de otro proyecto, sin confirmar o que no ves da `NOT_FOUND`; un `/storage`, una URL firmada o una URL externa dan `ASSET_ADAPTATION_REQUIRED`. Ya no hace falta que el asset sea de la misma page: reutiliza el que encuentres con `asset_list`. El asset sigue la audiencia de lo que lo usa.

- **Page (pai-page):** `page_read view=full` y luego `page_update` con CAS.
  - Imagen: bloque `{type: "figure", assetId, alt, caption, credit?}`. `assetId: null` mientras no exista el archivo; nunca inventes un id.
  - Video: bloque `{type: "video", assetId, caption?, poster?}`. `assetId` es un MP4 o WebM y `poster` (opcional) una imagen del proyecto que se ve antes de reproducir.
  - En un bloque `view` (skill `views`): `Image`, `Carousel` o `Video` (con `title` obligatorio). Solo se aceptan en una vista guardada en la page; `view_render` los rechaza. Fuera del Portal (la vista del MCP) se ve el texto alternativo en un recuadro.
  - En Markdown de la page: `![alt](/api/pages/assets/<assetId>)`.
- **Nota:** en su Markdown, `![alt](<href>)` con el `href` del asset (`/api/pages/assets/<assetId>`), y `note_update` con `expectedRevision`. Súbelo con `documentId` = el id de la nota: así un cliente también puede subirlo a su propia nota.
- **Pizarra:** en el `graph` de `whiteboard_create` o `whiteboard_update`, un nodo `{id, label, image: "<assetId>"}`. El nodo es la imagen con su texto debajo (`shape` se ignora). Solo imágenes `ready` que veas; si no → `invalid_input` «El asset «…» no es una imagen lista de este proyecto que puedas ver: búscala con asset_list (kind image).». Los videos no van en nodos.

### Borrar

`asset_delete {assetId}` es **irreversible**: confirma con la persona antes. Solo se borra si **ninguna** page, nota o pizarra vigente lo usa; si no, `CONFLICT` `ASSET_IN_USE`: quítalo antes de cada documento en `usedIn`. Solo el staff o quien lo subió puede borrarlo (`FORBIDDEN` «Solo el equipo de Pai o quien lo subió puede borrar este asset.»). `canDelete` de `asset_get` lo dice antes de intentarlo. Las versiones viejas que lo citaban muestran su texto alternativo.

## 6. Archivos de Recursos

1. `file_upload {projectId, contentType, size}` (≤100 MiB) devuelve una URL firmada que caduca en 5 min.
2. Haz el `PUT` de inmediato.
3. `file_create {projectId, name, fileKey, folder?, mimeType?, sizeBytes?, visibility}`. Sin `folder`, el archivo va a la raíz.
   - `visibility: "internal"` es solo para el staff;
   - `visibility: "shared"` la ve el cliente. Pregunta antes de compartir y manda siempre `visibility` explícita.
4. `file_update` renombra o mueve; `file_delete` es definitivo. Una carpeta vacía se borra con `folder_delete` (§9).

## 7. Mover, restaurar, borrar

- `page_move {path, newPath, summary}` reescribe los enlaces. Revisa `warnings` y avisa de los backlinks externos.
- `page_restore {versionId, …CAS}` crea una revisión nueva con el contenido de una versión anterior (`page_versions` para elegirla).
- **`page_delete` es un borrado duro:** se van versiones, comentarios e índice, `page_restore` no lo recupera, y devuelve los backlinks que quedan rotos.
  - Antes de borrar, `page_read` y confirma con la persona.
  - Si solo está desactualizada, actualízala o márcalo en su contenido.

## 8. Atributos de una page (fecha, responsable, estatus, etiquetas)

Toda page (pai-page o Markdown, notas incluidas) puede llevar cuatro atributos. Se muestran en el bloque «Propiedades» del Portal, bajo el título:

| Clave | Formato | Notas |
|---|---|---|
| `date` | `AAAA-MM-DD` (un día que exista) | |
| `owner` | id de usuario | Debe ser del equipo de Pai o miembro de la organización del proyecto. `milestone_owner_options` los lista. El cliente ve solo el nombre |
| `status` | `draft` \| `in_review` \| `approved` \| `archived` | Se lee «Borrador», «En revisión», «Aprobado» y «Archivado». Sin `status`, la page no tiene estatus (no es «Borrador») |
| `labels` | hasta 10 cadenas de hasta 40 caracteres, sin repetir (sin importar mayúsculas) | Son libres y por proyecto, sin catálogo ni tool que las liste. Antes de inventar una, reutiliza las que ya usa el proyecto (`attributes` de `page_list` / `page_read`) |

- **Leer:** `page_read` (view=full) los devuelve tipados en `attributes` (`{date, owner: {id, name} | null, status | null, labels[]}`). El frontmatter crudo sigue en `frontmatter`. `page_list` incluye `attributes` en cada page que tiene alguno.
- **Validar:** `page_validate {frontmatter}` usa el mismo esquema que el Portal y comprueba que el responsable tenga acceso. `content` es opcional. Cada problema llega en `issues` con `code: "PAGE_ATTRIBUTE_INVALID"` y `path: "frontmatter.<clave>"`.
- **Cambiar (staff):** `page_frontmatter_update {path, frontmatter, expectedRevision, summary?}` con un merge-patch: lo que mandas se escribe, `null` borra la clave y lo omitido se conserva. Usa `expectedRevision` = `revision` de `page_read`; ante `CONFLICT`, relee. Cada cambio queda en el historial de versiones. Sirve también en una pai-page (solo cambia metadatos, no el contenido).
- **Cambiar en una nota:** `note_update {attributes, expectedRevision}`, solo o junto con `markdown`. El cliente cambia fecha, estatus y etiquetas de sus notas, nunca el responsable (`FORBIDDEN`). `note_create` no acepta atributos: créala y después ponlos.
- **Error:** un valor fuera del esquema (fecha inexistente, estatus desconocido, 11 etiquetas, responsable sin acceso) llega como `BAD_REQUEST` con `<clave>: <mensaje>` y no se escribe nada. Corrige el valor y repite.

Tipo, audiencia y descripción se cambian como antes:
- tipo y audiencia: `page_frontmatter_update` (`type`, `audience`) o `note_audience_set` para una nota;
- título y descripción de una pai-page: `page_update`.

### Filtrar y ordenar por atributos

`page_list` y `page_search` aceptan los mismos filtros. Entre claves se combinan con Y; dentro de una clave, con O:
- `status`: 1 a 4 estatus (`["in_review", "approved"]`);
- `owner`: el nombre (sin distinguir mayúsculas) o, para staff, el id;
- `labels`: la page tiene **alguna** de ellas (1 a 10);
- `dateFrom` / `dateTo`: `AAAA-MM-DD`, ambos incluidos. **Un rango deja fuera las pages sin fecha**;
- `audience`: `client` o `internal`; `pathPrefix` (solo `page_list`) limita a una carpeta.

`page_list` ordena con `sort`: `path` (por defecto), `date` (la más reciente primero) o `status` (draft → in_review → approved → archived); las pages sin ese valor van al final. Sigue `nextCursor` **con el mismo `sort`**: un cursor de otro orden reinicia la lista sin error.

`page_search` no ordena ni pagina: busca los 50 mejores y luego filtra, así que con filtros puede devolver menos que `limit` aunque haya más. Para un inventario completo con filtros usa `page_list`.

```json
{ "organizationId": "…", "projectId": "…", "status": ["in_review"], "labels": ["pagos"], "dateFrom": "2026-10-01", "sort": "date" }
```

## 9. Notas, carpetas y sugerencias

**Carpetas:** `folder_create {parent, name}`: `parent` es `""` (la raíz de Recursos; en Portal y Console se llama «Recursos» y el selector la muestra como «Recursos (raíz)») o el `path` de una carpeta visible; `name` (1-120) en español, el segmento sale en slug («Actas de obra» → `actas-de-obra`). Del staff nace `internal` y en la ruta exacta (ocupada → `CONFLICT`). Devuelve el `path`: úsalo como carpeta de la nota. No hay renombrar ni mover carpetas.

**Borrar una carpeta** (`folder_delete {path, summary}`, irreversible): solo se borra **vacía a cualquier profundidad**, sin páginas ni archivos dentro ni en sus subcarpetas, también los internos; sus subcarpetas vacías se van con ella.
1. Revisa qué contiene: `page_list {pathPrefix: "<path>/"}` y `file_list`. Mueve (`page_move`, `file_update`) o borra (`page_delete`, `file_delete`) antes lo que tenga, confirmándolo con la persona.
2. Confirma el borrado y llama `folder_delete` con `summary` (motivo, ≤80; queda en la auditoría `folder.delete`).
3. Errores: la raíz (`""`) da `invalid_input` («La raíz de Recursos no se puede eliminar.»); si no la ves, `not_found`; con contenido visible para ti, `CONFLICT` (vacíala primero); «No puedes eliminar esta carpeta.» (`FORBIDDEN`) si no es tuya (un cliente solo borra carpetas que hizo un cliente, y todas sus subcarpetas también) o si la bloquea contenido que no ves: no reintentes, pide a Pai que la borre.
4. Su dirección corta da 404 después; una dirección por ruta redirige a la carpeta existente más cercana. Devuelve las rutas borradas (`deleted`) y la url de la carpeta padre.

**Notas** (Markdown, que también escribe el cliente):
- `note_create {path, title, markdown?, audience?, summary?}`. Del staff nace `internal` salvo `audience: "client"`; la de un cliente es siempre `client` y su ruta lleva un sufijo aleatorio: usa el `path` que devuelve. No acepta atributos: ponlos después (§8).
- **Sin `kb:`:** una nota no cita conocimiento («Una nota no lleva referencias kb: …»). Si hace falta citar, es una pai-page.
- `note_update {path, expectedRevision, markdown?, attributes?}`: `markdown` es el cuerpo **completo**. Una pai-page no es nota («Las páginas de Pai se editan con page_update»).
- **La nota de un cliente no se reescribe:** si la nota la creó un cliente, tu `markdown` no se escribe; el servidor lo convierte en sugerencias para el cliente y responde `{suggested: true, setId, threadId}`. No es un fallo: no reintentes; dile a la persona que quedó como sugerencia. Los `attributes` sí se escriben directo.
- `note_audience_set {path, audience}` (solo staff): `client` la publica a la organización; una nota de cliente no puede pasar a `internal`.
- Para convertir una nota en pai-page: `page_create {…, derivedFromPageId}` con el `document.id` de la nota (del mismo proyecto), o `page_migrate`.

**Sugerencias** (cambios revisables «Antes / Después» en vez de escribir):
- `page_suggest {path, baseRevision, suggestions, summary}`: solo un agente del staff. `baseRevision` = la revisión vigente de `page_read` (vieja → `CONFLICT`: relee y propone de nuevo).
  - En una pai-page, cada sugerencia lleva `blockId` y bloques completos: `replace` (`was` + `now`), `insert` (solo `now`, tras `blockId`), `delete` (solo `was`).
  - En una nota, `was`/`now` son `{text, range}` (offsets UTF-16; un `insert` con rango vacío) y el texto de `was` debe estar en ese rango.
  - El hilo nuevo es `client` si la page es para el cliente; si no, `team`.
- `page_suggestions {path, state: open|all}`: estados `pending`, `accepted`, `rejected`, `stale`, y `canDecide`.
- `page_suggestion_decide {setId, decisions}`: el staff siempre; en una nota también quien puede escribirla. Al no quedar pendientes, las aceptadas se aplican juntas en una revisión; las `stale` no. Úsala solo cuando la persona lo decida.
- Usa sugerencias, no `page_update`, cuando la page es de otra persona o del cliente, o cuando te pidan «propón cambios».

## 10. Comentarios

Un hilo va sobre `target = {kind: "page" | "knowledge" | "proposal", id}` (el `document.id` de la page, el id del nodo o de la propuesta).

**Ancla:** un comentario de page **exige** `anchor {exact, prefix?, suffix?, blockId?, nodeId?, elementId?}`; `exact` es el texto literal tal como sale en `page_read`.
- `{blockId, nodeId}`: un nodo de un diagrama de ese bloque (del proyecto o de la organización; si el hilo lo lee un cliente, el nodo debe ser `visibility: client`).
- `{blockId, elementId}`: un elemento del spec `pai-view@1` de ese bloque.
- `nodeId` y `elementId` van siempre con `blockId` y nunca juntos. En un nodo o una propuesta, omite el ancla.

**Audiencia** (`audience`, no cambia después; las respuestas la heredan):

| `audience` | Quién lo ve | Notas |
|---|---|---|
| `agent` | Solo su autor y su agente: llega a `agent_inbox` | Siempre tuyo: sin `audienceUserId` |
| `team` | El equipo de Pai | Solo staff; sin destinatario. **Es el valor por omisión del servidor para staff** |
| `client` | El cliente y Pai | Solo en una page `client` o una propuesta enviada |
| `person` | Una persona | `audienceUserId` de `comment_recipients {path}` (`kind: client \| staff`); el cliente destinatario debe ver la page |

- El compositor del Portal abre en «Para mi agente», pero **el servidor no**: si la persona quiere un hilo para su agente, pasa `audience: "agent"` explícito.
- `needsAgent: true` (solo staff, solo con `team` o `client`) lo pone en la bandeja de agentes del staff.
- `agent_inbox`: hilos `agent` propios sin responder y los `needsAgent`. Respóndelos con `comment_reply` (como la persona) o `page_comment_reply` (como agente, con `summary` y `resolve?`).
- `comment_edit {target, threadId, commentId, body}`: solo comentarios propios (o de este agente); queda «(editado)» y no cambia audiencia ni estado.
- `comment_send_to_agent {threadId, body?}` abre un hilo nuevo `agent` sobre el mismo fragmento, sin tocar el original. `comment_resolve`/`comment_reopen` solo en hilos de page.

Errores típicos: page sin `anchor` o con un `exact` que no coincide; `nodeId` sin `blockId`; `client` en una page interna; `needsAgent` con `agent` o `person`; editar el comentario de otra persona (`FORBIDDEN`).

## Qué no hacer

- **No** crees una page con `typeSlug` y un bloque `view` o `html`: da `bloque-no-permitido`.
- **No** dupliques en prosa una cifra que ya está en `facts` o `data-table`.
- **No** uses el campo `type` legacy (`arquitectura`, `reporte`…): usa `typeSlug`.
- **No** pegues HTML ni `<iframe>` en un `embed` ni en el Markdown: un `embed` guarda solo un enlace https, y el HTML interactivo va en un bloque `html`.
- **No** hagas `fetch` ni cargues scripts de otros hosts en un bloque `html`: los datos van dentro y los scripts de los cuatro CDNs.
- **No** pongas rutas en español ni con mayúsculas o espacios.
- **No** reescribas con `note_update` la nota de un cliente esperando que se guarde: queda como sugerencia.
- **No** omitas `audience` en un comentario «para mi agente»: el servidor lo deja para el equipo.
- **No** llames `folder_delete` sobre una carpeta con contenido esperando que se lo lleve: da `CONFLICT`. Vacíala antes.
- **No** uses `mode: "replace"` en `whiteboard_update` sin que te lo pidan: borra lo que dibujaron las personas. Tampoco escribas coordenadas ni elementos de Excalidraw: manda `graph` o `mermaid`.
