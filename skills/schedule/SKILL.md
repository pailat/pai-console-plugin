---
name: schedule
description: "Planea y lleva el Cronograma de un proyecto de Pai Console. Cubre hitos (fechas, monto, criterios de aceptación, línea base), dependencias entre hitos y entre tareas, tareas (nodos task de Knowledge), el tablero de Tareas y el cierre y la reapertura del proyecto. Úsalo cuando pidan plan de trabajo, cronograma, hitos, tareas, kanban, tablero, dependencias, línea base, el avance y los atrasos del proyecto, o cerrar o reabrir un proyecto."
argument-hint: "[proyecto] [qué planear o actualizar]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Cronograma y Tareas en Pai

Lee antes el skill `pai-console`.

## Modelo

- **Hitos** (`milestone_*`): entregas con fechas previstas y reales, criterios de aceptación, monto que se cobra (en centavos), estado (`pending`, `in_progress` o `completed`), responsable y línea base.
- **Tareas**: nodos `task` de Knowledge, ligados a un hito por `properties.milestoneId`.
  - `timeline_get` les calcula el estado (`scheduleLabel`: Pendiente, En curso, Atrasado, Completado o Cancelado, sobre el día de hoy en CDMX) y `blockedNow`.
- **Dependencias:**
  - entre hitos: `milestone_dependency_*`, fin a inicio, con `reason` y `visibility`;
  - entre tareas: `task_dependency_*`.

  En ambos casos el servidor rechaza duplicados y ciclos.
- **Tablero** (`task_board {milestoneId?, search?, columns?, limit, offset}`, paginado con `nextOffset`):

| Columna | Estado de la tarea |
|---|---|
| Borrador (`backlog`) | `draft` o `proposed` |
| Por hacer (`todo`) | `active` |
| Hecha (`done`) | resuelta `done` |
| Descartada (`discarded`) | resuelta `wont_do` o rechazada |

  Cada tarea trae su `revision`, su `citation` y en `moves` las transiciones posibles, con la tool y la entrada exactas: síguelas.

## Planear desde cero

1. **Lee lo que hay:** `timeline_get`, `milestone_list` y `task_board`. Si ya hay plan, ajústalo; no lo dupliques.
2. **Responsables:** `milestone_owner_options` da los `ownerUserId` válidos.
3. **Hitos, en orden:** `milestone_create` con:
   - `name` (en español), `description`, `acceptanceCriteria` (cómo se sabe que está hecho);
   - `startDate`, `endDate` (AAAA-MM-DD);
   - `amount` **en centavos** y `currency` **explícita** (`mxn` o `usd`). Por defecto es `usd`, pero las propuestas usan `mxn` por defecto: no lo dejes al azar;
   - `sequence` explícito (1, 2, 3…): sin él toma max+1 y puede chocar si hay otra escritura a la vez.
4. **Dependencias entre hitos:** `milestone_dependency_create {predecessorMilestoneId, successorMilestoneId, reason, visibility}`. `reason` explica por qué espera; `visibility` es `internal` o `client`, y con `client` el cliente lo lee.
5. **Tareas:** `knowledge_create` con `kind: "task"` y `status: "active"`. Lleva:
   - `properties.statement` (≥10);
   - `owner`, `startDate`, `dueDate`, `milestoneId` (del `milestone_list`);
   - `sources`: la reunión, la page o `{type:"chat"}`.

   Ejemplo validado: `${CLAUDE_PLUGIN_ROOT}/skills/schedule/examples/task.json`. `startDate` no puede ser posterior a `dueDate`.
6. **Dependencias entre tareas:** `task_dependency_create {predecessorTaskId, successorTaskId, reason, visibility}`. `visibility` es `internal` por defecto. Los ids son los uuid de los nodos `task`.
7. **Línea base:** cuando la persona confirme que el plan está acordado con el cliente, `milestone_baseline_capture` en cada hito. **Se captura una sola vez y no se mueve:** pide confirmación explícita.

## Llevar el día a día

| Evento | Qué hacer |
|---|---|
| Empezó un hito | `milestone_update {status:"in_progress", actualStartDate}` |
| Terminó un hito | `milestone_update {status:"completed", actualEndDate}`, tras confirmar que se cumplieron los `acceptanceCriteria` |
| Una tarea pasa de Borrador a Por hacer, o vuelve | `knowledge_update {ref, expectedRevision, status:"active"}` (o `"draft"`), sin `properties` |
| Se terminó una tarea | `knowledge_resolve {ref, outcome:"done", evidence, idempotencyKey}` |
| Se descarta una tarea | `knowledge_resolve {outcome:"wont_do", evidence}` |
| Cambian las fechas de una tarea | `knowledge_get` → `knowledge_update` con **todas** sus `properties` y las fechas nuevas |
| Reordenar hitos | `milestone_reorder {items:[{id, sequence}]}`. Ignora en silencio los ids que no son del proyecto: verifica después con `milestone_list` |

Notas:
- Una tarea cerrada no se reabre: si vuelve a hacer falta, crea otra y enlázala.
- Rechazar una tarea propuesta lo hace una persona desde el tablero.
- **`paymentStatus` de un hito no se edita a mano:** lo recalculan los pagos (skill `proposals-payments`). Un valor manual se pisa con el siguiente pago.

## Reportar el estado

1. Lee `timeline_get` (hitos, dependencias, `scheduleLabel`, `blockedNow`) y `task_board` (tareas por columna).
2. Resume: hitos por estado, tareas Atrasadas y bloqueadas (`blockedNow`), y lo próximo a vencer.
3. Si la persona lo pide, publícalo con `status_update_publish {health, headline, body}`: `health` es `on_track`, `at_risk` u `off_track`; `headline` ≤120 y `body` ≤600 caracteres. **El cliente lo ve al momento:** muéstrale el texto antes de publicar.

## Cerrar y reabrir un proyecto (staff)

1. `project_close_review`: lo que queda pendiente (`openTasks`, `unresolved` —preguntas, supuestos, riesgos—, `pendingSuggestions`, `counts`), cada uno con la `action` que lo cierra (por ejemplo, una tarea con `knowledge_resolve` `done` o `wont_do`). No bloquea: muéstraselo a la persona y resuelvan lo que decidan.
2. `project_close {status: "completed" | "cancelled", summary?}` (≤4000): deja el proyecto **en solo lectura**. Devuelve `merged[]`: cada producto que tocó registra `knowledge_merged`. `project_update` con `status` `completed` o `cancelled` también lo cierra. Confírmalo con la persona antes.
3. Con el proyecto cerrado, **toda escritura de contenido** (Conocimiento, también en un producto desde ese proyecto; pages, notas, carpetas, archivos, comentarios) responde `CONFLICT` «El proyecto está cerrado y es de solo lectura. Un miembro del equipo de Pai puede reabrirlo.», sin `cause`. No es una revisión vieja: no releas ni reintentes. Siguen abiertas las lecturas, las propuestas, los pagos, los hitos, los status updates y los vínculos de producto. `project_summary` trae `project.readOnly: true`.
4. `project_reopen {status?: "draft" | "planned" | "active" | "on_hold"}` (por defecto `active`): solo si la persona lo pide. Queda auditado. Un cliente no puede cerrar ni reabrir.

## Qué no hacer

- **No** borres hitos con pagos o CFDI (`milestone_delete` los deja huérfanos). Si sobra un hito, pregunta qué hacer con su cobro.
- **No** captures la línea base por iniciativa propia.
- **No** cierres ni reabras un proyecto por iniciativa propia, ni reintentes una escritura que respondió «El proyecto está cerrado».
- **No** crees tareas con kinds distintos de `task`, ni metas ni decisiones como tareas.
- **No** pongas montos en pesos o dólares enteros: van en centavos (`150000` = 1 500.00).
