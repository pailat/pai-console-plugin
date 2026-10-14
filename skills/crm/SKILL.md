---
name: crm
description: "CRM de Pai en Console (solo staff, MCP corp): leads, calificación, espacio de trabajo, oportunidades, pronóstico y la cadena envío → lead → oportunidad → propuesta → proyecto. Cubre revisar el tablero y lo que requiere atención, crear leads (desde Forms, referidos o a mano) sin duplicados, contactar, calificar, descalificar o ligar duplicados, abrir la organización y el proyecto de Descubrimiento, mover oportunidades por etapa, pausar, perder o ganar, interlocutores y probabilidad, y las tareas del CRM (tablero, detalle en Markdown, prioridad, etiquetas, reprogramar, reasignar y marcar hechas). Úsalo cuando pidan CRM, lead, prospecto, envío de Forms, calificar, pipeline, embudo, oportunidad, trato, pronóstico, forecast, «qué me toca», «mis tareas», tarea, seguimiento, «requiere atención», ganar o perder un trato."
argument-hint: "[lead, oportunidad u organización]"
compatibility: "Pai 0.2.5+ (MCP corp, staff con permisos crm:*)"
---

# CRM de Pai

Lee antes el skill `pai-console`. El CRM es **solo para el staff de Pai** en el MCP corp: un cliente nunca lo ve y el edge público no registra estas tools. Las tools no reciben `organizationId`/`projectId` de proyecto: trabajan sobre leads y oportunidades por su id.

Inventario completo: `${CLAUDE_PLUGIN_ROOT}/skills/pai-console/references/tools.md` § CRM.

## Antes de nada: permisos

`crm_access_get` (sin argumentos) dice qué puedes hacer. Una lista vacía es sin acceso.

| Permiso | Abre |
|---|---|
| `crm:access` | Ver el espacio: resumen, leads, envíos, fichas |
| `crm:edit` | Crear y mover leads, oportunidades, tareas e interlocutores; escribir notas |
| `crm:convert` | Ganar una oportunidad (`crm_opportunity_win`) |
| `crm:revenue` | Montos, pronóstico ponderado, `crm_opportunity_list`, `crm_opportunity_event_list` y ajustar probabilidad |
| `crm:purge` | Purgar basura sin cadena (`crm_lead_purge`) |
| `crm:import` | Importación histórica de un CRM anterior (`crm_lead_import`) |
| `crm:join` | Volverse admin de la organización de un lead (`crm_lead_workspace_join`). Abre sus proyectos, propuestas, pagos y recursos en el Portal, fuera del CRM. Sin él, la tool no aparece |

Todo permiso exige además `crm:access`. **Los permisos vienen de roles**, que solo los agrupan; las guardas preguntan por el permiso, nunca por el rol:

| Rol | Permisos |
|---|---|
| `crm.viewer` (Lector) | `crm:access` |
| `crm.sales` (Comercial) | `crm:access`, `crm:edit` |
| `crm.closer` (Cierre) | `crm:access`, `crm:edit`, `crm:convert`, `crm:revenue` |
| `crm.admin` (Administrador) | Todos menos `crm:join` |

- Un rol propio puede nombrar cualquier permiso, incluido `crm:join`.
- Mientras Administración no esté en el catálogo de permisos, un admin de plataforma los tiene todos.
- Una sesión suplantada no tiene ninguno.
- **Ningún rol limita la visibilidad a lo propio:** con `crm:access` se ven todos los leads, oportunidades y tareas. «Lo mío» es un filtro (`owner: "me"`), no un permiso.
- **Ser staff de una organización** (sin ser staff de Pai) no da el CRM: ahí cuenta el rol real.
- **Personas solo CRM:** quien no es staff de Pai pero tiene un rol de Console con `crm:access` recibe en el MCP corp solo las tools `crm_*`. Empieza por `crm_access_get` y `crm_overview_get`; no hay proyectos, Recursos ni Conocimiento.

Sin `crm:revenue` los montos no llegan: no los inventes ni los estimes.

## Reglas que el servidor hace cumplir

- **Nadie se queda sin siguiente paso.** Todo lead abierto (`new`, `contacted`) y toda oportunidad abierta tiene una tarea con fecha y **de quién depende**: `{body, dueAt, waitingOn, type?, detail?, priority?, tags?}` con `waitingOn` `pai` (de nosotros) o `client` (del cliente). La forma completa de la tarea está en § Tareas. Crear exige `firstTask`/`task`; mover de etapa o completar la última tarea exige `nextTask`. Propón la tarea con la persona; no inventes fechas.
- **`dueAt` en CDMX (`-06:00`).** Sin hora, el cierre del día hábil: `T18:00:00-06:00`, que Console muestra como «Sin hora» (todo el día en el calendario). Con hora (llamada, reunión), la suya: `T10:30:00-06:00`. **Nunca** medianoche ni mediodía UTC para decir «ese día»: salen como eventos con hora.
- **CAS:** toda escritura de un lead u oportunidad lleva `expectedRevision` (de `crm_lead_get`, `crm_lead_record` o `crm_opportunity_get`). Ante CONFLICT relee y vuelve a decidir.
- **Montos en centavos** (`4200000` = $42,000.00) y por moneda (`mxn`, `usd`). **MXN y USD nunca se suman**: reporta cada moneda aparte.
- **Archivar no es borrar.** Leads y oportunidades se archivan y vuelven con `*_unarchive`. Solo `crm_lead_purge` borra, y solo basura sin cadena.
- Todo cambio queda en el historial (`crm_lead_event_list`, `crm_opportunity_event_list`) marcado como vía MCP.

## Leer: qué está pasando

| Pregunta | Tool |
|---|---|
| ¿Cómo va el CRM? | `crm_overview_get {from?, to?}`: cifras, embudo de 90 días, «Por atender», tus tareas por día y conversiones. `period`: las series del tablero entre `from` y `to` (YYYY-MM-DD, días de CDMX; por omisión 30 días, máximo 366) contra el mismo número de días previos: leads y oportunidades creadas, ganadas y perdidas, tasa de cierre, mediana del primer contacto, tareas hechas, leads por origen y embudo, por día (≤31), semana (≤180) o mes. `ownerLoad`: lo abierto de cada responsable ahora |
| ¿Qué tareas tengo? | `crm_task_list` (por omisión, mis abiertas de la más vencida a la más lejana, con conteos por ventana) |
| ¿Qué requiere atención? | `crm_lead_list {waitingOn: "attention", owner: "me"}` y `crm_opportunity_list {waitingOn: "attention", owner: "me"}`: vencido, sin siguiente paso o en espera de nosotros hoy |
| Cifras del tablero de leads | `crm_lead_summary`: los tuyos que requieren atención, mediana del tiempo de respuesta (primer contacto), nuevos fuera de SLA (1 h hábil), abiertos sin siguiente paso |
| Pronóstico | `crm_opportunity_summary`: por moneda, ponderado y sin ponderar, tasa de cierre a 90 días, pausadas |
| Un lead a fondo | `crm_lead_record` (calificación, envío, espacio, oportunidades, nodos sembrados, actividades) |
| Una oportunidad a fondo | `crm_opportunity_get` (interlocutores, propuestas y versiones, actividades, historial) |
| ¿De dónde vino y en qué terminó? | `crm_trace_get {opportunityId, asOf?}`: envío → lead → espacio → oportunidad → propuesta → proyecto → hitos → producto |
| Propietarios posibles | `crm_owner_list` (ids para `ownerUserId`, `deliveryLeadUserId`) |

Filtros de `crm_lead_list`: `query`, `source`, `owner` (`me`, `none` o id), `period` (`30d`, `90d`, `year`, `all`; sin `period`, todos), `waitingOn` (`attention` requiere atención, `pai` en espera de nosotros, `client` en espera del cliente, `overdue` vencido, `none` sin siguiente paso, `outsideSla` primer contacto vencido sin importados), `archived: "1"`. `crm_opportunity_list` acepta los mismos `waitingOn` salvo `outsideSla` y suma `serviceLine`, `offering`, `kind`, `currency`, `market` (`mx`, `br`), `closeWindow` (`overdue`, `30d`, `90d`) y `organizationId`.

Para mostrarlo visual, compón con el skill `views` (`Stats`, `Kanban`, `DataTable`, `BarList`) y `view_render`, con la fecha de corte.

## Leads

Etapas: `new` → `contacted` → `qualified` (o `unqualified`) → `converted` (al ganar la primera oportunidad de su organización). Orígenes: `form`, `onboarding`, `manual`, `referral`, `mcp`; **no se cambian después**.

### Crear

1. **Desde un envío de Forms:** `crm_submission_get` → `crm_lead_create_from_submission {submissionId, ownerUserId, firstTask}`. Los datos vienen del envío; no los reescribas. Un envío basura sin lead: `crm_submission_spam` (lo archiva).
2. **Referido, manual o MCP:** si tienes correo, primero **`crm_lead_duplicates {email}`** (mismo correo, mismo dominio, organizaciones cliente con ese dominio); sin correo, busca por nombre o empresa con `crm_lead_list {query}`. Si hay coincidencia, muéstrala y decide con la persona. Luego `crm_lead_create {fullName, ownerUserId, firstTask, email?, phone?, company?, role?, source?, referredBy?, need?}`: necesita **al menos un correo, un teléfono o la empresa**. Avisa por correo al propietario (o al equipo con `crm:edit` si no hay).
3. **Importación histórica de un CRM anterior** (`crm_lead_import`, permiso `crm:import`): un registro por llamada, con su lead en su etapa **real** (también ganada o perdida) y sus fechas originales (`createdAt`, `firstContactedAt`), más `workspace`, `opportunity`, `notes` y `tasks` si los hay. `externalRef` (el id de origen) y `externalSystem` la hacen idempotente: repetirla responde `created: false` y no duplica. Con oportunidad, el lead va `qualified` (o `converted` si se ganó) y `workspace` es obligatorio. Pon el texto completo del origen en `notes`: nada se pierde. Solo para migrar un CRM anterior, nunca para un lead nuevo.

### Notas

`crm_lead_note_add {id, body}` y `crm_opportunity_note_add {id, body}` (≤20 000 caracteres) dejan una nota en el historial con autor y fecha. **No se editan:** para corregir, escribe otra. No mueven la etapa, el siguiente paso ni el último contacto: para registrar un contacto usa `crm_lead_update {stage: "contacted"}` o completa la tarea.

### Mover

| Paso | Tool | Exige |
|---|---|---|
| Contactado | `crm_lead_update {stage: "contacted", nextTask}` | Fija el primer contacto y da por hecha la tarea abierta |
| Editar datos o propietario | `crm_lead_update` | — |
| Tareas | `crm_task_create {record: {kind: "lead", id}, task}`, `crm_task_complete {taskId, nextTask?}` (también `crm_lead_task_create` y `crm_lead_task_complete`) | `nextTask` si es la última abierta. Ver § Tareas |
| **Calificar** | `crm_lead_qualify {qualification, workspace?, opportunity}` | Lead `contacted`, los cuatro criterios y espacio de trabajo |
| Descalificar | `crm_lead_disqualify {reason, note?, closeOpenTask?}` | Lead `new` o `contacted`; `other` exige `note` |
| Duplicado | `crm_lead_mark_duplicate {duplicateOfLeadId}` | El que sobrevive no puede ser duplicado de otro |
| Archivar / volver | `crm_lead_archive`, `crm_lead_unarchive` | — |

**Calificación (cuatro criterios):** `need` (qué necesita), `budgetRange` (`lt150`, `150-300`, `300-600`, `gt600` miles de MXN, o `unknown`), `timeline` y `decisionMaker`. Calificar siembra en Conocimiento los nodos del envío de Forms y crea la **primera oportunidad en Descubrimiento (10 %)** con su tarea. Pregunta lo que falte; no rellenes criterios.

```json
{ "leadId": "…", "expectedRevision": 3,
  "qualification": { "need": "Cobro recurrente con Stripe Billing", "budgetRange": "150-300", "timeline": "Arrancar en noviembre", "decisionMaker": "Directora de Finanzas" },
  "workspace": { "mode": "create_from_lead" },
  "opportunity": { "title": "Billing para suscripciones", "serviceLine": "stripe", "currency": "mxn", "amountMin": 15000000, "amountMax": 30000000, "expectedCloseAt": "2026-11-30",
    "task": { "body": "Enviar alcance de Descubrimiento", "dueAt": "2026-10-15T18:00:00-06:00", "waitingOn": "pai" } } }
```

`workspace` es `{mode: "create_from_lead", organizationName?}` o `{mode: "link_existing", organizationId}`; se omite si el lead ya tiene espacio.

**Motivos de descalificación:** `not_a_fit`, `no_budget`, `no_response`, `timing`, `competitor`, `other`. Spam no es una descalificación (archiva o purga) y un duplicado se liga. Un lead calificado ya no se descalifica.

### Espacio de trabajo (organización + proyecto)

1. `crm_lead_organization_suggestions {leadId}`: organizaciones parecidas por dominio, miembros y nombre, con su origen (`self_service`, `client`, `prospect`) y qué campos llenaría. **Nunca liga sola.**
2. Confirma con la persona: crear una nueva o ligar una existente.
3. `crm_lead_workspace_open {workspace}` (o dentro de `crm_lead_qualify`): crea o liga la organización (solo llena campos vacíos) y abre el proyecto «Descubrimiento» en borrador. **No se re-liga después.**
4. Ligar no te hace miembro. Para entrar: `crm_lead_workspace_join` («Entrar como staff», queda auditado).

### Purgar

`crm_lead_purge {reason: spam|test|mistake}` es **IRREVERSIBLE**: borra en duro un lead **sin cadena** (sin organización, proyecto, oportunidades, nodos ni duplicados) con sus tareas e historial. Con cadena, archívalo. Confirma con la persona siempre, también en staging y develop.

## Tareas

Las tareas viven en un **lead** abierto (`new`, `contacted`), una **oportunidad** abierta (también en pausa) o una **cuenta** (`record.kind: "account"`, `record.id` = `organizationId`). Son el tablero «Tareas» de Console.

**Columnas del tablero:**

| `state` | Columna | De dónde sale |
|---|---|---|
| `todo` | Por hacer | Abierta y sin empezar |
| `in_progress` | En curso | `crm_task_update {progress: "in_progress"}`; `progress: "todo"` la regresa |
| `waiting` | En espera del cliente | `waitingOn: "client"` |
| `done` | Hecha | `crm_task_complete` |

### Leer

- `crm_task_list`: por omisión, las abiertas del que pregunta, de la más vencida a la más lejana, con `counts` por ventana (`overdue`, `today`, `week`, `later`; días de CDMX).
  - Filtros: `owner` (`me`, `all` o un id de `crm_owner_list`), `status` (`open` o `done`), `subject` (`lead`, `opportunity` o `account`), `due`, `priority`, `tag` y `query` (texto de la tarea o del registro).
- `crm_task_get {taskId}`: todo, incluido `detail` (el Markdown) y su registro.
- `crm_task_tag_list`: las etiquetas del equipo, la más usada primero. **Revísala antes de inventar una etiqueta.**

### Crear

`crm_task_create {record: {kind, id}, task, ownerUserId?}`. Por omisión, el responsable es el propietario del registro, o tú.

| Campo | Qué va |
|---|---|
| `body` | **Título corto** (≤500): «Enviar el NDA», «Llamada de alcance». No metas el detalle aquí |
| `dueAt` | Fecha futura en CDMX. Sin hora: `2026-10-15T18:00:00-06:00` («Sin hora»). Con hora: la suya (`2026-10-15T10:30:00-06:00`). No la inventes: acuérdala con la persona |
| `waitingOn` | `pai` (de nosotros) o `client` (del cliente) |
| `type` | `todo` (por omisión), `call`, `email` o `meeting` |
| `priority` | `low`, `medium` o `high`; sin ella, sin prioridad |
| `tags` | Hasta 10, de ≤40 caracteres. Reusa las de `crm_task_tag_list` |
| `detail` | Notas, contexto o pasos en **Markdown** (≤20 000) |

La misma forma sirve para `firstTask`, `task` y `nextTask` en las demás tools del CRM.

**Cómo escribir `detail`:** es lo que ve la página de la tarea en Console, con el mismo editor que las notas.
- Empieza por el contexto en una o dos frases: por qué existe la tarea y qué la dispara.
- Sigue con los pasos como lista de verificación (`- [ ] …`) cuando haya más de uno.
- Pon enlaces Markdown a lo que haga falta (propuesta, page, correo), y nombres y fechas concretos.
- Sin encabezados `#` de primer nivel: el título ya es `body`.
- No pegues aquí datos sensibles que no necesite el equipo.

```json
{ "record": { "kind": "opportunity", "id": "…" },
  "task": { "body": "Enviar alcance de Descubrimiento", "dueAt": "2026-10-16T18:00:00-06:00", "waitingOn": "pai", "type": "email", "priority": "high", "tags": ["propuesta"],
    "detail": "Mariana pidió el alcance antes del comité del viernes.\n\n- [ ] Ajustar el SOW con las dos integraciones de Stripe\n- [ ] Validar montos con Finanzas\n- [ ] Enviar a mariana@cliente.mx con copia a Luis" } }
```

### Cambiar

- `crm_task_update {taskId, …}` cambia una tarea **abierta**:
  - `dueAt` reprograma (a fecha futura) y `ownerUserId` reasigna (de `crm_owner_list`);
  - también `waitingOn`, `type`, `priority` (`null` la quita), `progress` y `tags` (la **lista completa**: `[]` las quita);
  - `detail` cambia las notas en la misma tarea (`null` o vacío lo borra).
- **Un `body` nuevo no edita:** archiva la tarea y abre su corrección **con otro id**, el que devuelve. Usa ese id de ahí en adelante.
- Cada cambio queda en el historial; nada se borra.

### Cerrar

`crm_task_complete {taskId, nextTask?}` la marca hecha. Si es la **última abierta** de un lead u oportunidad abiertos, `nextTask` es obligatoria y se abre en el mismo registro: propón la siguiente con la persona. Devuelve la cerrada y la siguiente (`next`).

## Oportunidades

Etapas abiertas y su probabilidad: `discovery` 10 % → `scoping` 25 % → `proposal_sent` 50 % → `negotiation` 75 %. Cierres: `won` 100 %, `lost` 0 %. `on_hold` sale del pronóstico.

Tipos (`kind`): `new_business` (exige `leadId` de un lead calificado de la cuenta; abre proyecto), `expansion` (abre proyecto), `renewal` y `change_order` (nacen de una ganada con `parentOpportunityId` y usan su proyecto).

Líneas y ofertas (`offerings` deben ser de su `serviceLine`):
- `stripe`: billing, connect, payments, checkout, invoicing, tax, terminal, radar, identity
- `product_design`: app, dashboard, website
- `ai`: mcp_connector, ai_app, implementation_plan

Modelo comercial: `fixed_price`, `time_and_materials`, `retainer`.

Mercado (`market`): `mx` (México) o `br` (Brasil), o `null` si aún no se sabe. **No es la moneda**: un trato de Brasil puede cotizarse en USD. Se da al crear o con `crm_opportunity_update` (`null` lo quita) y filtra `crm_opportunity_list {market}`. `discoveryPaid` marca un Descubrimiento pagado.

### Crear

`crm_organization_list {query}` → `crm_organization_get {organizationId}` (leads calificados, personas del Portal, abiertas y ganadas) → `crm_opportunity_create {organizationId, kind, title, serviceLine, offerings, currency, amountMin, amountMax, expectedCloseAt, market?, discoveryPaid?, task, …}`. El título no repite el de otra abierta de la organización.

### Mover

| Paso | Tool | Exige |
|---|---|---|
| Cambiar etapa o datos | `crm_opportunity_update {stage, nextTask, …}` | `nextTask` al cambiar etapa; `proposal_sent` exige una propuesta **enviada** ligada (`proposalId`, skill `proposals-payments`) |
| Pausar | `crm_opportunity_hold {task}` | `task.dueAt` es la fecha de retomar; se reanuda con `update` y una etapa abierta |
| Perder | `crm_opportunity_lose {reason, note?, competitorName?}` | Motivos: price, timing, no_budget, competitor, no_response, no_decision, in_house, not_a_fit, other (`other` exige `note`) |
| Probabilidad | `crm_opportunity_probability {probability, reason}` o `{reset: true}` | `crm:revenue`; cambiar de etapa la regresa a la de la etapa |
| Interlocutores | `crm_opportunity_contact_add {leadId \| userId, role, isPrimary?}`, `_primary`, `_remove` | Roles: decision_maker, champion, finance, technical, user, other |
| Archivar / volver | `crm_opportunity_archive`, `crm_opportunity_unarchive` | — |

### Ganar

`crm_opportunity_win` es **IRREVERSIBLE** y requiere `crm:convert`. Antes de llamarla, reúne y confirma con la persona:

1. `acceptedProposalVersionId`: una versión `send` o `accept` de una propuesta del proyecto (de `crm_opportunity_get`). Si la propuesta estaba enviada, queda aceptada a nombre de `acceptedByName` o de quien decide.
2. `deliveryLeadUserId` (de `crm_owner_list`), `startAt` (YYYY-MM-DD), `serviceLine` y al menos una oferta.
3. Un interlocutor con rol **`decision_maker`**.

Efectos: la primera ganada de la organización convierte su lead y activa la cuenta; el proyecto pasa a planeado y se crea «Debrief de traspaso». **No copia conocimiento ni páginas.** Después sigue el skill `schedule` (hitos) y `proposals-payments`.

## Errores frecuentes

- Meter el detalle de una tarea en `body` en vez de `detail`, o inventar etiquetas sin mirar `crm_task_tag_list`.
- Seguir usando el id viejo de una tarea después de cambiarle el `body`.
- Mandar en `tags` solo la etiqueta nueva: reemplaza la lista completa.

- Crear un lead sin revisar `crm_lead_duplicates` (o `crm_lead_list` si no hay correo).
- Usar `crm_lead_import` para un lead nuevo, o reimportar con otro `externalRef` el mismo registro.
- Esperar que una nota (`*_note_add`) cuente como contacto o mueva la etapa.
- Escribir sin `expectedRevision` o con una vieja.
- Sumar MXN y USD en un total.
- Dar montos sin `crm:revenue` o inventar probabilidades.
- Marcar spam con `crm_lead_disqualify` (es archivar o purgar).
- Ligar una organización sin confirmar la sugerencia con la persona.
- Ganar sin `decision_maker` o sin una versión de propuesta enviada o aceptada.
