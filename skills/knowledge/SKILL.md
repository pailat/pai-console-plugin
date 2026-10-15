---
name: knowledge
description: "Crea y mantiene el Conocimiento (grafo de nodos y aristas) de un proyecto o de un producto de Pai Console. Cubre elegir el kind, plantillas, fuentes obligatorias, propuestas que confirma una persona, CAS con expectedRevision, enlaces según la ontología (incluido implemented_by módulo → componente), consultas estructuradas (knowledge_query), lotes atómicos (knowledge_batch) y el ciclo de vida (resolve, supersede, archive). Úsalo para registrar decisiones, reglas de negocio, riesgos, preguntas, supuestos, hechos, glosario, módulos o cualquier nodo, o para consultar el grafo. ERD, C4, pantallas y flujos tienen skills propios (erd, c4, screens, flows)."
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Conocimiento en Pai

Lee antes el skill `pai-console`. El grafo es la memoria del proyecto: cada nodo es una afirmación o un artefacto con su fuente; cada arista dice cómo se relacionan.

## Elegir el kind

Referencia completa, generada desde los contratos: `${CLAUDE_PLUGIN_ROOT}/skills/knowledge/references/kinds.md` (plantillas y ejemplos) y `${CLAUDE_PLUGIN_ROOT}/skills/knowledge/references/ontology.md` (relaciones permitidas). `knowledge_kinds` devuelve lo mismo desde el servidor; úsalo si dudas de la versión.

| Si es… | kind |
|---|---|
| Una meta medible con horizonte | `objective` |
| Una elección ya tomada, con contexto y consecuencias | `decision`; si es de arquitectura y formal, `adr` |
| Algo que el negocio exige («si X entonces Y») | `business_rule` |
| Un límite externo que no se elige | `constraint` |
| Algo que puede salir mal | `risk` |
| Algo que no sabemos | `question` |
| Algo que damos por cierto sin probarlo | `assumption` |
| Trabajo por hacer | `task` (skill `schedule`) |
| Un dato verificable con fuente | `fact`; una fuente externa, `reference` |
| Vocabulario | `glossary_term`; idea del dominio, `concept` |
| Un módulo funcional del producto | `module` |
| Pantalla, actor, o lo que la persona hace en una pantalla (`action`) | skill `screens` |
| Un recorrido con pasos y ramas (`flow`), el servicio que corre un paso (`integration`) | skill `flows` |
| Una prueba de un flujo (`flow_run`) | No se crea a mano: la crea `flow_run_start` (skill `flows`); `knowledge_create kind=flow_run` se rechaza |
| Modelo de datos, tabla | skill `erd` |
| Sistema, contenedor, componente | skill `c4` |
| Cómo se hace algo / qué evitar | `runbook`, `pattern`, `gotcha`, `antipattern` |
| Nada de lo anterior | `note`, y como último recurso |

## Reglas que el servidor impone a un agente

1. **`sources` obligatorio:** sin al menos una fuente da `SOURCE_REQUIRED`. Tipos:
   - `page` `{pageId, quote?}`;
   - `page_comment` `{pageId, threadId}`;
   - `url` `{url, accessedAt}`;
   - `repo` `{path, ref?}`;
   - `chat`;
   - `meeting` `{title, date}`;
   - `ckl` `{blockId}`.

   Las fuentes son estrictas: una clave extra se rechaza. `fact` y `reference` exigen fuente siempre.
2. **Lo que decide una persona queda como propuesta.** `objective`, `decision`, `adr`, `business_rule` y `constraint` se crean en `proposed`. Pedir `active` da `HUMAN_CONFIRMS`.
   - Confirmar o rechazar no es tarea del agente: no hay tool para eso. Lo hace una persona en el Portal o en Console.
   - Al terminar, **dile a la persona qué propuestas quedaron pendientes**, con sus citas `kb:`.
3. **Un nodo activo de esos kinds no se edita.** Para cambiarlo, crea el nuevo (también `proposed`). Cuando una persona lo active, `knowledge_supersede` reemplaza al viejo: exige que el nuevo esté `active`.
4. **Lo que ve el cliente lo cuida una persona.**
   - Un agente no edita, archiva ni desenlaza nodos visibles al cliente (`CLIENT_VISIBLE_REQUIRES_PERSON`). No lo rodees ocultándolo, editándolo y publicándolo otra vez: crea una propuesta interna de reemplazo o pídeselo a una persona.
   - En el MCP corp, el agente del **staff** sí puede cambiar la visibilidad (`internal` ↔ `client`) en un `knowledge_update` que **solo** lleve `visibility`; queda registrado con un warning. Hazlo al final y con el visto bueno de la persona (orden en el skill `flows`). En cualquier otro caso, `visibility:"client"` se baja a `internal` con un warning.
5. **Las plantillas son estrictas:** `properties` lleva exactamente las claves del kind. Una clave desconocida, o un Mermaid dentro (`MERMAID_NOT_ALLOWED`), se rechaza.
6. **Las referencias aceptan** `uuid`, `slug`, `kind/slug` o `kb:kind/slug@rN`. **Usa `kind/slug`**: es legible y no es ambiguo.

## Crear un nodo

1. `knowledge_search` con el tema y los kinds probables. Para ver todo lo de un kind en el proyecto, `knowledge_library {projectId, kinds}`. Para el bundle de contexto alrededor de un nodo o tema, `knowledge_context`.
2. Si existe algo equivalente: **actualízalo, enlázalo o, si lo contradice, propón el reemplazo**. No crees un duplicado.
3. `knowledge_create` con:
   - `kind`, `slug` (en inglés y kebab-case), `title` (en español, ≤200), `summary` (≤280);
   - `properties` según la plantilla, `sources`;
   - `links` (≤10 aristas creadas en la misma escritura);
   - `changeSummary` (≤80), `idempotencyKey` (8–128, estable).
4. Lee la respuesta:
   - `similar`: posibles duplicados. Si uno es el mismo nodo, archiva el tuyo con motivo o fusiona.
   - `warnings`: referencias sin resolver, visibilidad degradada.
   - La cita `kb:` del nodo, para dársela a la persona.

## Enlazar

`knowledge_link {rel, sourceRef, targetRef, evidence}`. `evidence` (≤500) dice por qué existe la arista. Las relaciones útiles:

| rel | Uso |
|---|---|
| `grounds` / `warrant` | La evidencia o el razonamiento que sostiene una decisión o una regla (Toulmin) |
| `supports` / `opposes` / `rebuttal` | A favor, en contra, excepción |
| `depends_on`, `implements`, `refers_to` | Dependencia, implementación, uso de un término |
| `constrains` | Una regla o restricción limita un módulo, una pantalla, un flujo… |
| `contains` | Jerarquía estructural (módulo → pantalla, data_model → entidad, component → component) |
| `offers` | Una pantalla ofrece una acción. No fija contenedor: la acción puede estar en varias pantallas |
| `triggers` | Una acción dispara un flujo o una integración, o un flujo dispara una integración («Pagar» corre Stripe) |
| `performs`, `navigates_to`, `uses` | También para acciones: el actor ejecuta la acción, la acción lleva a una pantalla, la acción usa entidades (`properties.mode`: create, update, read) |
| `tests` | Una prueba (`flow_run`) de un flujo. Solo la escribe `flow_run_start`: no la crees a mano |
| `relates_to` | Solo entre entidades del ERD, y se deriva de sus FK: no la crees a mano |

**`implemented_by` (módulo → componente):** dice en qué componente C4 se implementa un módulo funcional. Solo va de `module` a `component` y **los dos nodos tienen que ser del mismo producto** (créalos y enlázalos con el mismo `productId`, ver abajo). Errores: kinds al revés u otros → `ONTOLOGY`; un nodo de proyecto o de organización → `cause.code: IMPLEMENTED_BY_NEEDS_PRODUCT`; productos distintos → `IMPLEMENTED_BY_ACROSS_PRODUCTS`. Mover fuera del producto un nodo con esa arista da `PRECONDITION_FAILED` `HAS_IMPLEMENTED_BY`.

Si da `ONTOLOGY`, ese par no admite esa relación. Busca en `${CLAUDE_PLUGIN_ROOT}/skills/knowledge/references/ontology.md` una que sí lo admita; no fuerces otra parecida solo para que pase.

## Conocimiento de un producto (`productId`)

Las tools `knowledge_*` (y `knowledge_view`, `knowledge_query`, `knowledge_batch`, `task_board`) aceptan `productId`: entonces trabajan sobre el conocimiento **de ese producto** (su arquitectura y funcionamiento vigentes), no el del proyecto.
- `projectId` sigue siendo obligatorio y el proyecto tiene que tocar el producto (`product_link_project`, skill `products`). Si no: `BAD_REQUEST` con `cause.code: PRODUCT_NOT_IN_SCOPE`; usa uno de los productos del proyecto (`product_get`).
- `knowledge_create {productId}` hace nacer el nodo en el producto. Una `task` nunca: `TASK_NEEDS_PROJECT`.
- Sin `productId`, `knowledge_query` ya incluye los nodos de los productos que toca el proyecto y los de la organización enlazados; con él, acota a ese producto.
- Al cerrar un proyecto, cada producto que tocó registra `knowledge_merged`.

## Consultar el grafo: `knowledge_query`

Para preguntas estructuradas («los requisitos activos con prioridad alta», «las pantallas que contiene este módulo», «los riesgos que afectan a un componente»), mejor que una búsqueda por tema:
- `kinds` (obligatorio), `status` (por defecto draft, proposed y active), `properties` `{clave: [valores]}` de la plantilla, `tags`;
- `scope {nodeId, revision}`: descendientes por `contains`;
- `related {node, rels, direction: in|out|both, depth 1-3}`: vecindad;
- `pattern {steps}` (≤4 pasos): el primero sin `via`, los demás con `via {rel, direction}`;
- `limit` ≤200; si viene `truncated`, acota.

Errores: `BAD_REQUEST` con `cause.code: QUERY` e `issues` (propiedad que no es de la plantilla, paso sin `via`, arista que la ontología no admite); `TIMEOUT` `QUERY_TIMEOUT`: acota `kinds`, `scope`, `depth` o el patrón.

## Muchas escrituras juntas: `knowledge_batch`

Hasta 200 operaciones atómicas (`create` con ref local `$nombre`, `update`, `link`, `unlink`, `supersede`, `archive`, `resolve`, `set-status`) con un `idempotencyKey`, `changeSummary`, `sources` del lote y `productId?`.
- **Revisa siempre `status` de la respuesta.** Un lote rechazado **no es un error del MCP**: llega con `status: "rejected"` y, por operación fallida, `results[i].error {code, message, allowedTargets?, suggestedRels?, currentRevision?}`. No se escribió nada (las operaciones `ok: true` anteriores se revirtieron).
- **`set-status` lo decide una persona:** desde el MCP siempre eres un agente, así que un lote con `set-status` vuelve `rejected` con `HUMAN_CONFIRMS` (ATE-184). Quita esa operación y deja los nodos `proposed`.
- La clave de un lote rechazado no se consume: corrige y reintenta con la misma. La misma clave con otra entrada da `IDEMPOTENCY_MISMATCH`; con la misma entrada, `replayed: true`.

## Actualizar (CAS)

1. `knowledge_get` del nodo: `revision` y `properties` completas.
2. Modifica **sobre esa copia**.
3. `knowledge_update {ref, expectedRevision, changeSummary, …}`. Si mandas `properties`, se **reemplazan completas**: lo que omitas dentro de ellas se borra. Para cambiar solo `status`, `title`, `summary`, `tags` o `sources`, no mandes `properties`.
4. Ante `CONFLICT` (`REVISION`): relee, integra y reintenta una vez.

## Ciclo de vida

| Situación | Tool |
|---|---|
| Se respondió una `question` o se probó o refutó una `assumption` | `knowledge_resolve` con `outcome` (`answered`, `confirmed` o `refuted`), `evidence`, `idempotencyKey` y un nodo de resolución: `resolution` (borrador en línea) **o** `resolutionRef`, nunca ambos. Queda enlazado con `supports` u `opposes` |
| Se mitigó un `risk` o terminó una `task` | `knowledge_resolve` con `outcome` `done` o `wont_do` |
| Un nodo nuevo reemplaza a uno viejo | `knowledge_supersede {oldRef, newRef, evidence}`. El nuevo debe estar `active` |
| Ya no aplica | `knowledge_archive {reason}`, reversible con `knowledge_revive`. Los nodos no se borran |
| Lo consultaste y te sirvió | `knowledge_observe` (barato, no audita) |

## Salud del grafo

- `knowledge_audit` lista nodos débiles, delgados (sin justificación), huérfanos, preguntas sin resolver y pantallas con **«fuente sin conectar»** (`unconnectedSources`: un bloque de `content` con `source` en texto en vez de `{ref}`, skill `screens`). Úsalo al cerrar una sesión de modelado y dale el resultado a la persona.
- `knowledge_impact` (`maxDepth` ≤3) dice qué se afecta si cambia un nodo. Úsalo antes de proponer el reemplazo de una decisión.
- `knowledge_graph {projectId?}` muestra la estructura: nodos con su grado, aristas y hubs (`hubThreshold`). Úsalo para encontrar los nodos centrales y los huérfanos de un proyecto o de toda la organización.
- **Conocimiento de la organización:** un nodo puede no tener proyecto y ser **de la organización** (un glosario común, reglas del cliente, sistemas compartidos).
  - `knowledge_library` y `knowledge_graph` aceptan tres alcances en `projectId`: un proyecto (sus nodos más los de la organización enlazados a él), `"organization"` (solo los de la organización), o ninguno (todo).
  - En los resultados, esos nodos traen `project: null`.
  - **Antes de crear en un proyecto, busca también en `"organization"`.** Si ya existe ahí, enlázalo (`knowledge_link` acepta su uuid como `targetRef`) en vez de duplicarlo.
  - Crear un nodo de la organización o mover un nodo entre proyecto y organización **no está en el MCP**: lo hace una persona en el Portal o en Console. Propónselo si un nodo de proyecto debería ser común.
  - En el Portal, la ficha de un nodo de la organización está en `/organization/knowledge/<nodeId>`.
- Las tareas siempre viven en su proyecto.

## Lo que ve el cliente (ATE-237)

El cliente ve **Conocimiento en solo lectura** en el Portal y en su MCP:
- solo los nodos `visibility: "client"`, y las aristas cuyas **dos puntas** son visibles para él;
- sus tools de Conocimiento son lecturas del proyecto: `knowledge_kinds`, `knowledge_search`, `knowledge_get`, `knowledge_impact` y `knowledge_view`;
- **no** tiene escrituras (`knowledge_create`, `update`, `link`, `batch`…), ni `knowledge_context`, `knowledge_audit` o `knowledge_query`, ni el Conocimiento de la organización (`knowledge_library`, `knowledge_graph`). Tareas (`task_board`) sigue siendo del staff;
- en Flujos ve solo los flujos `client`; una ref a un nodo interno sale como «Interno» (skill `flows`).

Por eso, antes de publicar un nodo, piensa qué arrastra: un nodo `client` cuyo vecino es `internal` se ve sin esa arista. Y escribe `title`, `summary` y `properties` de un nodo `client` como algo que el cliente va a leer: sin correos, ids del staff ni notas internas.

## Qué no hacer

- **No** crees nodos sin fuente real ni inventes fuentes: si la fuente es la conversación, usa `{type:"chat"}` y dilo.
- **No** encadenes reintentos de `HUMAN_CONFIRMS`: es un límite, no un error.
- **No** uses `note` para lo que tiene kind propio.
- **No** pongas en `properties` texto que debería ser otro nodo: una decisión dentro de las notas de un riesgo debe ser una `decision` enlazada.
