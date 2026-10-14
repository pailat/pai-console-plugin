# Inventario de tools del MCP corp de Pai (0.2.5+)

**Fuente:** pai-portal `feat/0.2.5/reui` @ db7700fe (incluye CRM-1..4, el bloque html de ATE-204 y CRM #178) (`apps/api/src/modules/mcp/tools/*.ts`).

Las tools declaran sus anotaciones, y la guarda las lee de `hooks/tools.json`, que se genera desde el servidor. Todas las tools de proyecto reciben `organizationId` y `projectId`. Las `knowledge_*`, `task_board` y `knowledge_view` aceptan además `productId` para trabajar sobre el conocimiento de un producto que el proyecto toca. Con el proyecto cerrado, toda escritura de contenido responde `CONFLICT` «El proyecto está cerrado…».

**Leyenda:**
- **L**: lectura. Pasa libre en cualquier entorno.
- **E**: escritura. En producción pide confirmación.
- **IRR**: irreversible. En producción la confirmación dice qué arrastra.

## Identidad y descubrimiento

| Tool | Tipo | Nota |
|---|---|---|
| `whoami` | L | Staff o cliente, scopes |
| `organization_list` | L | `query`, `limit` ≤100 |
| `organization_get` | L | Miembros, invitaciones y proyectos |
| `organization_create` | E | Quien llama entra como admin; con `ownerEmail` envía una invitación |
| `organization_slug_set` | E | Staff. Cambia el slug de la organización en las URLs del Portal; el anterior redirige y no se reutiliza |
| `organization_update` | E | Requiere ser owner o admin de esa organización, como el resto de ajustes de la organización. Nombre visible o logo (`logo` = `fileKey` de `organization_logo_upload_url`, "" lo quita); el slug no cambia |
| `organization_logo_upload_url` | E | URL firmada para el PUT del logo de la organización: **solo PNG** ≤10 MB. Es el avatar del selector y de Ajustes › General, no el logo del tema (que acepta SVG): sube los dos |
| `organization_member_role_set` | E | owner, admin o member (`memberId` de `organization_get`); nunca deja la organización sin owner |
| `organization_member_remove` | E | Quita al miembro y libera su asiento; no quita al último owner |
| `organization_invitation_cancel` | E | El enlace del correo deja de servir |
| `me_profile_update` | E | Tu nombre visible o tu foto (`image` = `fileKey` de `me_avatar_upload_url`) |
| `me_avatar_upload_url` | E | URL firmada para el PUT de tu foto (PNG ≤10 MB) |
| `project_list` | L | |
| `project_summary` | L | |
| `project_status` | L | |
| `project_activity` | L | |
| `project_create` | E | `status` empieza en draft; las fechas van en ISO |
| `project_update` | E | |
| `project_slug_set` | E | Staff. Cambia el slug del proyecto en las URLs del Portal; el anterior redirige |
| `project_invite_client` | E | Envía un correo con la invitación |
| `project_delete` | E · IRR | **Borra en cascada los pagos y los CFDI** |
| `project_close_review` | L | Lo pendiente antes de cerrar (tareas, preguntas, riesgos, sugerencias), con la acción que lo cierra; no bloquea |
| `project_close` | E | Deja el proyecto en solo lectura (`completed` o `cancelled`); cada producto registra `knowledge_merged` |
| `project_reopen` | E | Reabre un proyecto cerrado; queda auditado |
| `status_update_list` | L | |
| `status_update_publish` | E | El cliente lo ve al momento |
| `brief_list` | L | |
| `brief_get` | L | |
| `brief_agenda` | L | |
| `brief_update_status` | E | new → reviewing → converted |

## Tema de la organización

La marca que ven el Portal y las vistas del cliente. Solo staff en el MCP corp. Flujo: `organization_theme_get` → `organization_theme_preview` → `organization_theme_save_draft` → `organization_theme_publish`. Guía completa, mapa de tokens y verificación en el Portal: skill `theme`.

| Tool | Tipo | Nota |
|---|---|---|
| `organization_theme_get` | L | Tema publicado, borrador con sus problemas (AA, esquema, logo) y versiones. Léelo antes de editar |
| `organization_theme_preview` | L | Valida un tema (o el borrador) sin guardar: problemas de contraste AA, CSS, los `shells` que puede elegir (`id` null = el de Pai) y muestra |
| `organization_theme_save_draft` | E | Borrador nuevo; lo publicado no cambia. Los problemas de AA se permiten en borrador |
| `organization_theme_publish` | E | El cliente lo ve en su siguiente carga. Se rechaza si no cumple AA, esquema o logos |
| `organization_theme_revert` | E | Copia una versión como borrador y, salvo `publish: false`, la publica |
| `organization_theme_logo_upload_url` | E | URL firmada (5 min) para el PUT del logo: PNG, WebP o SVG ≤512 KB, con el `contentType` y `size` declarados |
| `organization_theme_logo_confirm` | E | Tras el PUT (`storageKey` = `fileKey`): valida el logo y devuelve el objeto `{storageKey, contentType, bytes}`. Va **completo** en `theme.logo.light` o `theme.logo.dark`; un string da «se esperaba objeto, recibido texto» |

## Recursos

| Tool | Tipo | Nota |
|---|---|---|
| `folder_create` | E | Carpeta vacía en Recursos (`parent` "" = General); devuelve su `path` para `note_create` |
| `folder_delete` | E · IRR | Solo carpetas vacías a cualquier profundidad (páginas y archivos, internos incluidos); se lleva sus subcarpetas vacías. `summary` obligatorio (≤80, queda en la auditoría). General no se borra (`invalid_input`); con contenido → `CONFLICT`; no es tuya o la bloquea contenido que no ves → `FORBIDDEN` |
| `note_create` | E | Nota Markdown; la del staff nace interna salvo `audience: client` |
| `note_update` | E | Cuerpo y atributos con `expectedRevision`. En la nota de un cliente, un agente de Pai solo **propone** sugerencias (`{suggested: true}`) |
| `note_audience_set` | E | `client` la publica para la organización; `internal` la deja al equipo de Pai |
| `page_frontmatter_update` | E | Merge-patch del frontmatter: audiencia y atributos (date, owner, status, labels) con `expectedRevision` |
| `page_projection` | L | Dibuja un bloque `projection` de una page (C4, ERD, pantalla, flujo) como el lector del Portal |
| `page_suggest` | E | Propone cambios revisables («Antes / Después») a una page o nota en vez de escribirlos; `baseRevision` de `page_read` |
| `page_suggestion_decide` | E | Acepta o rechaza las sugerencias de un set; las aceptadas se aplican juntas |
| `quiz_respond` | E | Responde un bloque quiz en nombre de la persona; cada intento cuenta |
| `page_catalog` | L | Unos 35 KB: bloques, reglas, JSON Schema y vistas. Prefiere las referencias de los skills `resources` y `views` |
| `page_types` | L | Lista, o el detalle de un `slug` con su `authoringGuide` |
| `page_validate` | L | Valida sin guardar `content` y/o `frontmatter` (atributos); devuelve `issues` y `warnings` (avisos del bloque `html`) |
| `page_list` | L | Filtros `status`, `owner`, `labels`, `dateFrom`/`dateTo`, `audience`, `pathPrefix`; `sort` path, date o status; sigue `nextCursor` con el mismo `sort`. Trae `attributes` |
| `page_search` | L | `limit` ≤50, sin cursor ni orden; mismos filtros que `page_list` (busca 50 y filtra: puede traer menos que `limit`) |
| `page_read` | L | `view`: summary, content o full. Solo `full` sirve para escribir. Trae `attributes` tipados y las `projections` resueltas |
| `page_versions` | L | Pagina con `nextCursor` |
| `page_version` | L | |
| `page_comprehension` | L | Antes de reescribir una page |
| `page_create` | E | `summary` ≤80; `idempotencyKey` obligatoria; sin imágenes; `derivedFromPageId` liga la page a la nota de origen. Avisos en `warnings` |
| `page_update` | E | Reemplazo completo, con CAS |
| `page_restore` | E | Restaura una versión como revisión nueva |
| `page_move` | E | Reescribe los enlaces; revisa los `warnings` |
| `page_migrate` | E | Convierte Markdown legacy a Pages |
| `page_asset_upload` | E | URL firmada para subir con PUT (png/jpeg/webp/gif ≤10 MB) |
| `page_comment_reply` | E | |
| `page_delete` | E · IRR | Borrado duro, sin papelera |
| `file_list` | L | |
| `file_get` | L | |
| `file_download_url` | L | |
| `file_upload` | E | URL firmada (≤100 MiB, caduca en 5 min) |
| `file_create` | E | Registra el archivo subido |
| `file_update` | E | |
| `file_delete` | E · IRR | |

## Conocimiento

| Tool | Tipo | Nota |
|---|---|---|
| `knowledge_query` | L | Consulta el grafo por propiedad, etiqueta, contención (`scope`), vecindad (`related`) o camino tipado (`pattern`, ≤4 pasos); `limit` ≤200 |
| `knowledge_batch` | E | Hasta 200 operaciones atómicas (create, update, link, unlink, supersede, archive, resolve) con refs `$nombre` e `idempotencyKey`; `set-status` lo decide una persona y un agente recibe `HUMAN_CONFIRMS` |
| `knowledge_kinds` | L | Catálogo de kinds, plantillas y ontología. Referencia local: `skills/knowledge/references/` |
| `knowledge_search` | L | Búsqueda por tema; `limit` ≤25, sin cursor |
| `knowledge_library` | L | **Inventario y tabla de la organización:** `projectId` + `kinds`, paginado con `limit`/`offset` hasta `total`; búsqueda híbrida con `query` |
| `knowledge_graph` | L | Nodos, aristas y hubs de la organización o de un proyecto |
| `knowledge_get` | L | `ref`: uuid, slug, `kind/slug` o `kb:` |
| `knowledge_context` | L | |
| `knowledge_impact` | L | |
| `knowledge_audit` | L | |
| `knowledge_view` | L | Vista ERD (`view: "erd"`) o C4 (`view: "c4"`, `level`) derivada del grafo: datos, Mermaid y `url` del Portal |
| `task_board` | L | Tablero de Tareas: columnas, `revision` y `moves` de cada tarea |
| `knowledge_create` | E | Un agente debe dar `sources` |
| `knowledge_update` | E | Con `expectedRevision`; si llevas `properties`, las reemplaza completas |
| `knowledge_link` | E | |
| `knowledge_observe` | E | Señal de uso; no cambia la revisión |
| `knowledge_resolve` | E | Cierra una question, assumption, risk o task |
| `knowledge_supersede` | E | El nodo nuevo debe estar `active` |
| `knowledge_revive` | E | |
| `knowledge_archive` | E | Reversible con `knowledge_revive` |
| `knowledge_unlink` | E · IRR | |

## Cronograma

| Tool | Tipo | Nota |
|---|---|---|
| `timeline_get` | L | |
| `milestone_list` | L | |
| `milestone_get` | L | |
| `milestone_owner_options` | L | |
| `milestone_create` | E | `amount` en centavos; moneda por defecto **usd** |
| `milestone_update` | E | |
| `milestone_reorder` | E | |
| `milestone_dependency_create` | E | finish_to_start; rechaza ciclos |
| `milestone_dependency_update` | E | |
| `milestone_dependency_delete` | E | |
| `task_dependency_create` | E | Entre nodos `task`; rechaza ciclos |
| `task_dependency_update` | E | |
| `task_dependency_delete` | E | |
| `milestone_baseline_capture` | E · IRR | Una sola vez por hito |
| `milestone_delete` | E · IRR | Sus CFDI quedan sin hito |

## Propuestas y pagos

| Tool | Tipo | Nota |
|---|---|---|
| `proposal_list` | L | |
| `proposal_get` | L | |
| `payment_list` | L | |
| `payment_file_download_url` | L | URL firmada de 60 s para un comprobante o el PDF/XML de una factura (`fileId` de `payment_list`); úsala de inmediato y no la guardes |
| `proposal_save` | E | Solo borradores; moneda por defecto **mxn** |
| `proposal_set_status` | E · IRR | draft → sent → accepted/rejected |
| `milestone_proposal_link` | E | |
| `payment_file_upload` | E | PDF ≤10 MB; PUT antes de 5 min |
| `payment_cfdi_import` | E · IRR | El emisor debe ser el RFC de Pai |
| `payment_record` | E · IRR | Dinero; recalcula el estado de pago de los hitos |
| `payment_void` | E · IRR | Anula el pago para siempre |

## Productos

| Tool | Tipo | Nota |
|---|---|---|
| `product_list` | L | `missing[]` y `hint` dicen qué falta |
| `product_get` | L | |
| `product_provisioning_get` | L | |
| `product_logs` | L | |
| `product_member_list` | L | |
| `product_create` | E | |
| `product_update` | E | |
| `product_environment_set` | E | Solo registro en la base de datos de Pai |
| `product_environment_remove` | E | Solo registro en la base de datos de Pai |
| `product_domain_set` | E | Solo registro en la base de datos de Pai |
| `product_domain_remove` | E | Solo registro: no desconecta en Railway |
| `product_link_set` | E | |
| `product_link_remove` | E | |
| `product_link_project` | E | `role` creates, improves (por defecto) o maintains; habilita `productId` en `knowledge_*` desde el proyecto |
| `product_unlink_project` | E | |
| `product_member_add` | E | |
| `product_member_update` | E | |
| `product_request_status` | E | `live` necesita que otra persona lo apruebe |
| `product_decide_status` | E | |
| `product_provision` | E · IRR | Crea el repo en GitHub y el proyecto en Railway |
| `product_deploy` | E · IRR | En production exige `commitSha` |
| `product_variables_set` | E · IRR | Los valores nunca se devuelven; `redeploy` |
| `product_domain_attach` | E · IRR | Devuelve los `dnsRecords` |
| `product_production_access_set` | E · IRR | Redespliega producción |
| `product_member_remove` | E · IRR | |

## Vistas (UI generativa)

| Tool | Tipo | Nota |
|---|---|---|
| `view_catalog` | L | Catálogo `pai-view@1` (componentes, props, reglas, ejemplo); con `types`/`group`, `recipe` o `recipeGroup`, uno a la vez. Prefiere la referencia del skill `views` |
| `view_render` | L | Dibuja en la conversación una vista que compones (`{title, spec}`); la valida y no guarda nada. `organizationId` la pinta con el tema de esa organización |

Además, en los hosts con MCP Apps, las lecturas con una vista propia se dibujan solas como una vista de Pai: `project_summary`, `project_list`, `project_activity`, `project_close_review`, `status_update_list`, `timeline_get`, `milestone_list`, `payment_list`, `proposal_list`, `task_board`, `file_list`, `page_list`, `page_suggestions`, `page_comprehension`, `page_knowledge_health`, `page_projection`, `agent_inbox`, `knowledge_library`, `knowledge_graph`, `knowledge_view`, `organization_theme_preview`, las lecturas del CRM (`crm_overview_get`, `crm_lead_list`, `crm_lead_summary`, `crm_lead_get`, `crm_lead_record`, `crm_lead_event_list`, `crm_lead_duplicates`, `crm_lead_organization_suggestions`, `crm_submission_get`, `crm_opportunity_list`, `crm_opportunity_summary`, `crm_opportunity_get`, `crm_opportunity_event_list`, `crm_trace_get`) y `view_render`. `knowledge_view` y `page_projection` se dibujan en el lienzo (`ui://pai/canvas.html`). Las demás lecturas (detalles, búsquedas, validaciones, catálogos) devuelven solo datos y texto (ATE-203).

## CRM (solo staff, permisos `crm:*`)

Detalle y reglas en el skill `crm`. Toda escritura de lead u oportunidad lleva `expectedRevision`; montos en centavos, MXN y USD nunca se suman.

| Tool | Tipo | Nota |
|---|---|---|
| `crm_access_get` | L | Tus permisos: crm:access, edit, convert, revenue, purge, import, join. Vienen de roles (`crm.viewer`, `crm.sales`, `crm.closer`, `crm.admin` o propios) |
| `crm_overview_get` | L | Portada de /crm: cifras, embudo, «Por atender», tus tareas, conversiones. `from`/`to` (YYYY-MM-DD, ≤366 días) dan las series del periodo contra el anterior; `ownerLoad` es lo abierto de cada responsable |
| `crm_owner_list` | L | Propietarios posibles (ids para `ownerUserId`) |
| `crm_submission_get` | L | Un envío de Forms y el lead que generó |
| `crm_submission_spam` | E | Archiva el envío sin crear lead |
| `crm_lead_list` | L | Filtros `query`, `source`, `owner`, `period`, `waitingOn` (`attention` = requiere atención, `none`, `outsideSla`…), `archived` |
| `crm_lead_summary` | L | Tuyos que requieren atención, tiempo de respuesta, fuera de SLA, sin siguiente paso |
| `crm_lead_get` | L | El lead con su `revision`, siguiente paso y cadena |
| `crm_lead_record` | L | Ficha completa: calificación, envío, espacio, oportunidades, nodos sembrados, actividades |
| `crm_lead_event_list` | L | Historial del lead (≤200) |
| `crm_lead_duplicates` | L | **Antes de crear:** mismo correo, mismo dominio, organizaciones cliente |
| `crm_lead_organization_suggestions` | L | Organizaciones parecidas y qué campos llenaría; nunca liga |
| `crm_lead_create` | E | Referido, manual o MCP; `firstTask` obligatoria; `phone` opcional; avisa por correo |
| `crm_lead_import` | E | `crm:import`. Importación histórica de un CRM anterior (lead, organización, oportunidad, notas y tareas en su etapa real y con sus fechas); `externalRef` la hace idempotente (`created: false` al repetir) |
| `crm_lead_note_add` | E | Nota en el historial del lead (≤20 000 caracteres); no se edita: para corregir, escribe otra. No mueve etapa ni siguiente paso |
| `crm_lead_create_from_submission` | E | Lead desde un envío de Forms |
| `crm_lead_update` | E | Datos, propietario o `stage: contacted` (exige `nextTask`) |
| `crm_lead_task_create` | E | Tarea en un lead (`crm_task_create` sirve también para oportunidades y cuentas) |
| `crm_lead_task_complete` | E | Cierra una tarea; `nextTask` si es la última |
| `crm_lead_qualify` | E | Cuatro criterios + espacio; siembra nodos y crea la primera oportunidad (Descubrimiento) |
| `crm_lead_disqualify` | E | Motivo de la lista; archiva |
| `crm_lead_mark_duplicate` | E | Liga al lead que sobrevive y archiva |
| `crm_lead_workspace_open` | E | Crea o liga la organización y abre el proyecto «Descubrimiento»; no se re-liga |
| `crm_lead_workspace_join` | E | `crm:join`. Te agrega como admin de la organización del lead; auditado. Sin el permiso no aparece |
| `crm_lead_archive` | E | Sale del tablero sin borrarse |
| `crm_lead_unarchive` | E | |
| `crm_lead_purge` | E · IRR | Borrado duro de basura sin cadena (`spam`, `test`, `mistake`); `crm:purge` |
| `crm_organization_list` | L | Organizaciones para abrir una oportunidad (≤20) |
| `crm_organization_get` | L | Leads, personas del Portal, oportunidades abiertas y ganadas de la cuenta |
| `crm_opportunity_list` | L | `crm:revenue`. Filtros de etapa, propietario, siguiente paso (`waitingOn`), línea, oferta, tipo, moneda, mercado (`market` mx/br), cierre |
| `crm_opportunity_summary` | L | Pronóstico por moneda, tasa de cierre, las tuyas que requieren atención, pausadas |
| `crm_opportunity_get` | L | Con `revision`, interlocutores, propuestas y versiones, actividades, historial |
| `crm_opportunity_event_list` | L | Cambios recientes de todas las oportunidades; `crm:revenue` |
| `crm_trace_get` | L | La cadena envío → … → producto, con `asOf` |
| `crm_opportunity_create` | E | `kind`, línea y ofertas, montos en centavos, `market` (mx/br, no es la moneda), `discoveryPaid`, `task` obligatoria |
| `crm_opportunity_update` | E | Etapa abierta (exige `nextTask`), datos (también `market` y `discoveryPaid`), propietario o propuesta ligada |
| `crm_opportunity_hold` | E | En pausa; `task.dueAt` = fecha de retomar |
| `crm_opportunity_lose` | E | Perdida con motivo de la lista |
| `crm_opportunity_probability` | E | Ajuste 0–100 con motivo, o `reset`; `crm:revenue` |
| `crm_opportunity_note_add` | E | Nota en el historial de la oportunidad (≤20 000 caracteres); no se edita ni mueve la etapa |
| `crm_opportunity_contact_add` | E | Interlocutor por `leadId` o `userId` con su rol |
| `crm_opportunity_contact_primary` | E | Marca el principal |
| `crm_opportunity_contact_remove` | E | Lo quita (queda en la historia) |
| `crm_opportunity_archive` | E | Sale del tablero y del pronóstico |
| `crm_opportunity_unarchive` | E | |
| `crm_opportunity_win` | E · IRR | Gana con versión de propuesta aceptada, responsable de entrega, inicio y `decision_maker`; `crm:convert` |

### Tareas del CRM

La tarea es `{body, dueAt, waitingOn, type?, detail?, priority?, tags?}`: `body` es el título corto, `detail` las notas en Markdown (≤20 000), `type` todo|call|email|meeting, `priority` low|medium|high y `tags` hasta 10. La misma forma vale en `firstTask`, `task` y `nextTask`. `dueAt` va en CDMX: sin hora, `T18:00:00-06:00` («Sin hora»); con hora, la suya. Nunca medianoche ni mediodía UTC.

| Tool | Tipo | Nota |
|---|---|---|
| `crm_task_list` | L | Tablero de Console (todo, in_progress, waiting, done). Por omisión, tus abiertas de la más vencida, con `counts` (overdue, today, week, later). Filtros `owner` (me, all o id), `status`, `subject`, `due`, `priority`, `tag`, `query` |
| `crm_task_get` | L | Una tarea con `detail`, tipo, prioridad, etiquetas, estado y registro |
| `crm_task_tag_list` | L | Etiquetas del equipo, la más usada primero; revísalas antes de crear una |
| `crm_task_create` | E | En un lead abierto, una oportunidad abierta o en pausa, o una cuenta (`record.kind` account, `id` = organizationId). Fecha futura; `ownerUserId` opcional |
| `crm_task_update` | E | Reprograma, reasigna, cambia `waitingOn`, `type`, `priority`, `tags` (lista completa), `detail` o `progress` (todo ↔ in_progress). Un `body` nuevo archiva la tarea y abre su corrección **con otro id** |
| `crm_task_complete` | E | La marca hecha; `nextTask` obligatoria si es la última abierta de un lead u oportunidad abiertos |

## Otros

| Tool | Tipo | Nota |
|---|---|---|
| `comment_list` | L | Pagina con cursor |
| `comment_history` | L | |
| `comment_recipients` | L | |
| `comment_create` | E | `audience` agent, team (por omisión para staff), client o person (`audienceUserId`); `needsAgent`; una page exige `anchor` |
| `comment_reply` | E | |
| `comment_edit` | E | Solo comentarios propios; queda «(editado)» |
| `comment_resolve` | E | Solo en hilos de page |
| `comment_reopen` | E | Solo en hilos de page |
| `comment_send_to_agent` | E | Solo en hilos de page; abre un hilo `agent` nuevo (con `body` opcional) sin tocar el original |
| `agent_list` | L | |
| `agent_get` | L | |
| `agent_create` | E | |
| `agent_update` | E | |
| `agent_delete` | E · IRR | Para retirarlo, usa `status: archived` |
| `credit_balance` | L | |
| `credit_transactions` | L | No hay compra ni ajuste |
