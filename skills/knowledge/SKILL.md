---
name: knowledge
description: Crea y mantiene el Conocimiento (grafo de nodos y aristas) de un proyecto de Pai Console. Cubre elegir el kind, plantillas, fuentes obligatorias, propuestas que confirma una persona, CAS con expectedRevision, enlaces según la ontología y el ciclo de vida (resolve, supersede, archive). Úsalo para registrar decisiones, reglas de negocio, riesgos, preguntas, supuestos, hechos, glosario, módulos o cualquier nodo. ERD, C4 y pantallas tienen skills propios (erd, c4, screens).
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
| Pantalla, flujo, actor | skill `screens` |
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
4. **La visibilidad para el cliente la decide una persona.** `visibility:"client"` se baja a `internal` con un warning.
   - Un agente no edita, archiva ni desenlaza nodos visibles al cliente (`CLIENT_VISIBLE_REQUIRES_PERSON`).
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
| `relates_to` | Solo entre entidades del ERD, y se deriva de sus FK: no la crees a mano |

Si da `ONTOLOGY`, ese par no admite esa relación. Busca en `${CLAUDE_PLUGIN_ROOT}/skills/knowledge/references/ontology.md` una que sí lo admita; no fuerces otra parecida solo para que pase.

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

- `knowledge_audit` lista nodos débiles, delgados (sin justificación), huérfanos y preguntas sin resolver. Úsalo al cerrar una sesión de modelado y dale el resultado a la persona.
- `knowledge_impact` (`maxDepth` ≤3) dice qué se afecta si cambia un nodo. Úsalo antes de proponer el reemplazo de una decisión.
- `knowledge_graph {projectId?}` muestra la estructura: nodos con su grado, aristas y hubs (`hubThreshold`). Úsalo para encontrar los nodos centrales y los huérfanos de un proyecto o de toda la organización.
- `knowledge_library` sin `projectId` busca en **toda la organización**: sirve para reutilizar conocimiento de otro proyecto del mismo cliente (cítalo; no lo copies).

## Qué no hacer

- **No** crees nodos sin fuente real ni inventes fuentes: si la fuente es la conversación, usa `{type:"chat"}` y dilo.
- **No** encadenes reintentos de `HUMAN_CONFIRMS`: es un límite, no un error.
- **No** uses `note` para lo que tiene kind propio.
- **No** pongas en `properties` texto que debería ser otro nodo: una decisión dentro de las notas de un riesgo debe ser una `decision` enlazada.
