# Inventario de tools del MCP corp de Pai (0.2.5)

**Fuente:** pai-portal `release/0.2.5` (`apps/api/src/modules/mcp/tools/*.ts`) y el PR #139.

**Leyenda:**
- **L**: lectura. Pasa libre en cualquier entorno.
- **E**: escritura. En producción pide confirmación.
- **IRR**: irreversible. En producción la confirmación dice qué arrastra.

Todas las tools de proyecto reciben `organizationId` y `projectId`.

## Identidad y descubrimiento

| Tool | Tipo | Nota |
|---|---|---|
| `whoami` | L | Staff o cliente, scopes |
| `organization_list` | L | `query`, `limit` ≤100, sin cursor |
| `organization_get` | L | Miembros, invitaciones y proyectos |
| `organization_create` | E | Quien llama entra como admin; con `ownerEmail` envía una invitación |
| `project_list` / `project_summary` / `project_status` / `project_activity` | L | |
| `project_create` / `project_update` | E | `status` empieza en draft; las fechas van en ISO |
| `project_invite_client` | E | Envía un correo con la invitación |
| `project_delete` | E · IRR | **Borra en cascada los pagos y los CFDI** |
| `status_update_list` | L | |
| `status_update_publish` | E | El cliente lo ve al momento |
| `brief_list` / `brief_get` / `brief_agenda` | L | |
| `brief_update_status` | E | new → reviewing → converted |

## Recursos

| Tool | Tipo | Nota |
|---|---|---|
| `page_catalog` | L | Unos 35 KB: bloques, reglas, JSON Schema y vistas. Prefiere `skills/resources/references/` |
| `page_types` | L | Lista, o el detalle de un `slug` con su `authoringGuide` |
| `page_validate` | L | Valida sin guardar; devuelve `issues` |
| `page_list` | L | Pagina con `cursor` (= path) |
| `page_search` | L | `limit` ≤50, sin cursor |
| `page_read` | L | `view`: summary, content o full. Solo `full` sirve para escribir |
| `page_versions` / `page_version` | L | |
| `page_comprehension` | L | Antes de reescribir una page |
| `page_create` | E | `summary` ≤80; `idempotencyKey` obligatoria; sin imágenes |
| `page_update` | E | Reemplazo completo, con CAS |
| `page_restore` | E | Restaura una versión como revisión nueva |
| `page_move` | E | Reescribe los enlaces; revisa los `warnings` |
| `page_migrate` | E | Convierte Markdown legacy a Pages |
| `page_asset_upload` | E | URL firmada para subir con PUT (png/jpeg/webp/gif ≤10 MB) |
| `page_comment_reply` | E | |
| `page_delete` | E · IRR | Borrado duro, sin papelera |
| `file_list` / `file_get` / `file_download_url` | L | |
| `file_upload` / `file_create` / `file_update` | E | URL firmada (≤100 MiB, caduca en 5 min) → `file_create` |
| `file_delete` | E · IRR | |

## Conocimiento

| Tool | Tipo | Nota |
|---|---|---|
| `knowledge_kinds` | L | Catálogo de kinds, plantillas y ontología. Referencia local: `skills/knowledge/references/` |
| `knowledge_search` | L | `limit` ≤25, sin cursor |
| `knowledge_get` | L | `ref`: uuid, slug, `kind/slug` o `kb:` |
| `knowledge_context` / `knowledge_impact` / `knowledge_audit` | L | |
| `knowledge_library` / `knowledge_graph` | L | Del PR #139; puede no existir todavía |
| `task_board` | L | Del PR #139; puede no existir todavía |
| `knowledge_view` | L | **No usar** hasta que se unifique (#138/#139) |
| `knowledge_create` | E | Un agente debe dar `sources` |
| `knowledge_update` | E | Reemplaza las `properties` completas; `expectedRevision` obligatorio |
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
| `timeline_get` / `milestone_list` / `milestone_get` / `milestone_owner_options` | L | |
| `milestone_create` / `milestone_update` / `milestone_reorder` | E | `amount` en centavos; moneda por defecto **usd** |
| `milestone_dependency_create/update/delete` | E | finish_to_start; rechaza ciclos |
| `task_dependency_create/update/delete` | E | Entre nodos `task` |
| `milestone_baseline_capture` | E · IRR | Una sola vez por hito |
| `milestone_delete` | E · IRR | Sus CFDI quedan sin hito |

## Propuestas y pagos

| Tool | Tipo | Nota |
|---|---|---|
| `proposal_list` / `proposal_get` / `payment_list` | L | |
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
| `product_list` / `product_get` / `product_provisioning_get` / `product_logs` / `product_member_list` | L | `missing[]` y `hint` dicen qué falta |
| `product_create` / `product_update` | E | |
| `product_environment_set/remove`, `product_domain_set/remove`, `product_link_set/remove`, `product_link_project` / `product_unlink_project` | E | Solo registro en la base de datos; no tocan Railway |
| `product_member_add/update` | E | |
| `product_request_status` / `product_decide_status` | E | `live` necesita que otra persona lo apruebe |
| `product_provision` | E · IRR | Crea el repo en GitHub y el proyecto en Railway |
| `product_deploy` | E · IRR | En production exige `commitSha` |
| `product_variables_set` | E · IRR | Los valores nunca se devuelven; `redeploy` |
| `product_domain_attach` | E · IRR | Devuelve los `dnsRecords` |
| `product_production_access_set` | E · IRR | Redespliega producción |
| `product_member_remove` | E · IRR | |

## Otros

| Tool | Tipo | Nota |
|---|---|---|
| `comment_list` / `comment_history` / `comment_recipients` | L | Paginan con cursor |
| `comment_create` / `comment_reply` / `comment_resolve` / `comment_reopen` / `comment_send_to_agent` | E | resolve, reopen y send_to_agent solo funcionan en hilos de page |
| `agent_list` / `agent_get` | L | |
| `agent_create` / `agent_update` | E | |
| `agent_delete` | E · IRR | Para retirarlo, usa `status: archived` |
| `credit_balance` / `credit_transactions` | L | No hay compra ni ajuste |
