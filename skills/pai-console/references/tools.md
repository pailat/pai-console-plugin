# Inventario de tools del MCP corp de Pai (0.2.5+)

**Fuente:** pai-portal `feat/0.2.5/reui` (`apps/api/src/modules/mcp/tools/*.ts`).

Las tools declaran sus anotaciones, y la guarda las lee de `hooks/tools.json`, que se genera desde el servidor. Todas las tools de proyecto reciben `organizationId` y `projectId`.

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
| `project_list` | L | |
| `project_summary` | L | |
| `project_status` | L | |
| `project_activity` | L | |
| `project_create` | E | `status` empieza en draft; las fechas van en ISO |
| `project_update` | E | |
| `project_slug_set` | E | Staff. Cambia el slug del proyecto en las URLs del Portal; el anterior redirige |
| `project_invite_client` | E | Envía un correo con la invitación |
| `project_delete` | E · IRR | **Borra en cascada los pagos y los CFDI** |
| `status_update_list` | L | |
| `status_update_publish` | E | El cliente lo ve al momento |
| `brief_list` | L | |
| `brief_get` | L | |
| `brief_agenda` | L | |
| `brief_update_status` | E | new → reviewing → converted |

## Tema de la organización

La marca que ven el Portal y las vistas del cliente. Flujo: `organization_theme_get` → `organization_theme_preview` → `organization_theme_save_draft` → `organization_theme_publish`.

| Tool | Tipo | Nota |
|---|---|---|
| `organization_theme_get` | L | Tema publicado, borrador con sus problemas (AA, esquema, logo) y versiones. Léelo antes de editar |
| `organization_theme_preview` | L | Valida un tema (o el borrador) sin guardar: problemas de contraste AA, CSS y muestra |
| `organization_theme_save_draft` | E | Borrador nuevo; lo publicado no cambia. Los problemas de AA se permiten en borrador |
| `organization_theme_publish` | E | El cliente lo ve en su siguiente carga. Se rechaza si no cumple AA, esquema o logos |
| `organization_theme_revert` | E | Copia una versión como borrador y, salvo `publish: false`, la publica |
| `organization_theme_logo_upload_url` | E | URL firmada (5 min) para el PUT del logo: PNG, WebP o SVG ≤512 KB, con el `contentType` y `size` declarados |
| `organization_theme_logo_confirm` | E | Tras el PUT: valida el logo y devuelve la referencia para `theme.logo.light` o `theme.logo.dark` |

## Recursos

| Tool | Tipo | Nota |
|---|---|---|
| `page_catalog` | L | Unos 35 KB: bloques, reglas, JSON Schema y vistas. Prefiere las referencias de los skills `resources` y `views` |
| `page_types` | L | Lista, o el detalle de un `slug` con su `authoringGuide` |
| `page_validate` | L | Valida sin guardar; devuelve `issues` |
| `page_list` | L | Pagina con `nextCursor` (= path) |
| `page_search` | L | `limit` ≤50, sin cursor |
| `page_read` | L | `view`: summary, content o full. Solo `full` sirve para escribir |
| `page_versions` | L | Pagina con `nextCursor` |
| `page_version` | L | |
| `page_comprehension` | L | Antes de reescribir una page |
| `page_create` | E | `summary` ≤80; `idempotencyKey` obligatoria; sin imágenes |
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
| `product_link_project` | E | |
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
| `view_catalog` | L | Catálogo `pai-view@1` (componentes, props, reglas, ejemplo). Prefiere la referencia del skill `views` |
| `view_render` | L | Dibuja en la conversación una vista que compones (`{title, spec}`); la valida y no guarda nada |

Además, en los hosts con MCP Apps, las lecturas con una vista propia se dibujan solas como una vista de Pai: `project_summary`, `project_list`, `project_activity`, `status_update_list`, `timeline_get`, `milestone_list`, `payment_list`, `proposal_list`, `task_board`, `file_list`, `page_list`, `page_suggestions`, `page_comprehension`, `page_knowledge_health`, `agent_inbox`, `knowledge_library`, `knowledge_graph`, `knowledge_view`, `organization_theme_preview` y `view_render`. Las demás lecturas (detalles, búsquedas, validaciones, catálogos) devuelven solo datos y texto (ATE-203).

## Otros

| Tool | Tipo | Nota |
|---|---|---|
| `comment_list` | L | Pagina con cursor |
| `comment_history` | L | |
| `comment_recipients` | L | |
| `comment_create` | E | |
| `comment_reply` | E | |
| `comment_resolve` | E | Solo en hilos de page |
| `comment_reopen` | E | Solo en hilos de page |
| `comment_send_to_agent` | E | Solo en hilos de page |
| `agent_list` | L | |
| `agent_get` | L | |
| `agent_create` | E | |
| `agent_update` | E | |
| `agent_delete` | E · IRR | Para retirarlo, usa `status: archived` |
| `credit_balance` | L | |
| `credit_transactions` | L | No hay compra ni ajuste |
