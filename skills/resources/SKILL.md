---
name: resources
description: Crea y mantiene Recursos de un proyecto de Pai Console. Cubre pages (pai-page) con tipo y bloques, vistas con layout canvas y bloque view (catálogo pai-view@1), imágenes (assets) y archivos. Úsalo cuando pidan una page, documento, reporte, guía, PRD, SOW, arquitectura, tablero, dashboard, vista o pantalla visual, subir imágenes o documentos, o mover, restaurar o borrar una page.
argument-hint: "[proyecto] [tema o tipo de recurso]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Recursos en Pai: pages, vistas, imágenes y archivos

Lee antes el skill `pai-console`.

**Referencias, generadas desde los contratos:**
- `${CLAUDE_PLUGIN_ROOT}/skills/resources/references/page-types.md`: tipos built-in con sus secciones y bloques permitidos, límites y reglas;
- para componer vistas (`pai-view@1`), el skill **`views`**, con su catálogo y sus recetas.

Úsalas en lugar de `page_catalog`, que pesa unos 35 KB. Llama a `page_catalog` o a `page_types` solo si sospechas que el entorno tiene otra versión, o para ver los tipos propios de la organización o del proyecto.

## 1. Decide qué recurso es

| Necesitas… | Recurso |
|---|---|
| Un documento con estructura conocida (nota, guía, decisión, reporte, proceso, overview, PRD, SOW, arquitectura, discovery, inventario de diseño) | Page `layout: "document"` **con `typeSlug`** del tipo built-in. Sus secciones obligatorias mandan |
| Un tablero, reporte visual, mockup de pantalla o página libre | Page `layout: "canvas"` con un bloque **`view`**, **sin `typeSlug`**: ningún tipo built-in admite `view` |
| Un archivo binario (PDF, hoja de cálculo, contrato) | Archivo de Recursos (§6), no una page |
| Conocimiento atómico (decisión, regla, entidad, componente) | Un nodo de Knowledge (skill `knowledge`), no una page |

Si dudas entre page y nodo, piensa en el uso. **Una page se lee de corrido; un nodo se consulta, se enlaza y se reemplaza.** Una page puede citar nodos y un nodo puede citar una page (`sources: [{type:"page", pageId}]`).

## 2. Crear una page

1. **Busca:** `page_search` con el tema y `page_list` (sigue `nextCursor`) para ver la estructura de rutas. Si existe una page para lo mismo, actualízala (§4).
2. **Elige el tipo:** `${CLAUDE_PLUGIN_ROOT}/skills/resources/references/page-types.md`, o `page_types {slug}` para el `authoringGuide` completo y su ejemplo.
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
   - `audience`: `equipo` (interna) o `cliente` (la ve el cliente). Si no te lo dijeron, pregunta; si nadie decide, usa `equipo`;
   - `content`, `summary` (≤80, como un mensaje de commit);
   - `idempotencyKey`: `page-<proyecto>-<ruta-con-guiones>`.
7. **Lee la respuesta** (`warnings`, `document.revision`) y da a la persona:
   - la ruta y la revisión;
   - el enlace del Portal: `https://app.pai.lat/organization/projects/<projectId>/resources/<path>` en producción (en staging, la misma ruta en el Portal de staging).

   El campo `url` de la respuesta trae una ruta legacy (`/portal/…/pages/…`): no la uses como enlace.

Ejemplos validados:
- `${CLAUDE_PLUGIN_ROOT}/skills/resources/examples/report-page.json`: tipo `report`, con sus cinco secciones obligatorias;
- vistas en canvas: ejemplos en `${CLAUDE_PLUGIN_ROOT}/skills/views/examples/`.

## 3. Vistas (`view`, catálogo `pai-view@1`)

Tableros, mockups de pantallas, reportes visuales y comparativos se componen con el skill **`views`**: catálogo, recetas validadas, reglas de datos y diseño, y errores frecuentes. Aquí solo lo esencial de la page que la contiene:
- `layout: "canvas"` y un bloque `{id, type: "view", title, spec}`;
- **sin `typeSlug`**;
- valida con `page_validate` antes de guardar.

## 4. Actualizar una page

1. Si vas a reescribir, primero `page_comprehension`: sus preguntas más falladas dicen qué explicar mejor.
2. `page_read {path, view: "full"}`. Guarda `document.id` y `document.revision`.
3. Modifica **sobre ese contenido completo**. `page_update` **reemplaza** la page entera: nunca partas de `summary`, `content` parcial ni de `page_version`.
4. `page_validate` → `page_update {path, expectedDocumentId, expectedRevision, content, summary}`.
   - Para quitar el tipo: `detachType: true`. `typeSlug: null` no se acepta.
5. Ante `CONFLICT`: relee, integra y reintenta una vez.
6. Si `page_create` respondió con `replayed`, la page ya existía con esa clave: **relee** antes de actualizar, porque la revisión de la respuesta puede ser vieja.

## 5. Imágenes (assets)

Las imágenes son privadas de su page:
1. Crea la page **sin** imágenes. Un `figure` lleva `assetId: null` mientras no exista el archivo; nunca inventes un `assetId`.
2. `page_asset_upload {path, filename, contentType, size}`. Formatos png, jpeg, webp o gif, de hasta 10 MB; `size` en bytes **exactos**.
3. Sube con `PUT` a la URL firmada, con los headers devueltos y exactamente esos bytes. Por ejemplo, `curl -X PUT --data-binary @file …` con los headers que indica la respuesta.
4. `page_read view=full` y luego `page_update`, con el `assetId` en el bloque `figure`, o `/api/pages/assets/<assetId>` en el Markdown.
5. **Nunca guardes la URL firmada** en la page ni en un nodo.

## 6. Archivos de Recursos

1. `file_upload {projectId, contentType, size}` (≤100 MiB) devuelve una URL firmada que caduca en 5 min.
2. Haz el `PUT` de inmediato.
3. `file_create {projectId, name, fileKey, folder?, mimeType?, sizeBytes?, visibility}`. Sin `folder`, el archivo va a la raíz.
   - `visibility: "internal"` es solo para el staff;
   - `visibility: "shared"` la ve el cliente. Pregunta antes de compartir y manda siempre `visibility` explícita.
4. `file_update` renombra o mueve; `file_delete` es definitivo.

## 7. Mover, restaurar, borrar

- `page_move {path, newPath, summary}` reescribe los enlaces. Revisa `warnings` y avisa de los backlinks externos.
- `page_restore {versionId, …CAS}` crea una revisión nueva con el contenido de una versión anterior (`page_versions` para elegirla).
- **`page_delete` es un borrado duro:** se van versiones, comentarios e índice, `page_restore` no lo recupera, y devuelve los backlinks que quedan rotos.
  - Antes de borrar, `page_read` y confirma con la persona.
  - Si solo está desactualizada, actualízala o márcalo en su contenido.

## Qué no hacer

- **No** crees una page con `typeSlug` y un bloque `view`: da `bloque-no-permitido`.
- **No** dupliques en prosa una cifra que ya está en `facts` o `data-table`.
- **No** uses el campo `type` legacy (`arquitectura`, `reporte`…): usa `typeSlug`.
- **No** pegues HTML ni `<iframe>`: un `embed` guarda solo un enlace https.
- **No** pongas rutas en español ni con mayúsculas o espacios.
