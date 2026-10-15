---
name: flows
description: "Flujos de un proyecto de Pai Console (ATE-230): el flujo como entidad con pasos (inicio, paso, decisión, fin), ramas etiquetadas y referencias a actor, pantalla, acción e integración, y sus pruebas «Probar como…». Cubre flow_list, flow_get, flow_create, flow_save (CAS con expectedRevision, grafo o Mermaid), flow_version_bump y flow_run_start/step/finish/list/get, los nodos action e integration (simulada con sampleResponse y sampleCases), el checklist para que un flujo se pueda probar y el orden para publicarlo al cliente. Úsalo cuando pidan un flujo, un recorrido, un journey, un diagrama de proceso con ramas, probar un flujo, «Probar como…», simular una integración o dejar un flujo listo para el cliente."
argument-hint: "[proyecto] [flujo a crear, corregir o probar]"
compatibility: "Pai 0.2.5+ (MCP corp; flow_* en develop desde d65d611ac)"
---

# Flujos en Pai: `flow_*` y `flow_run_*`

Lee antes el skill `pai-console`. Los nodos `actor`, `screen` y `action` se documentan con el skill `screens`, y el resto del Conocimiento con el skill `knowledge`.

Un flujo **describe, se ve y se prueba**:
- es un nodo `flow` de Conocimiento y, a la vez, una entidad con sus pasos como filas (`flow_step`) y sus ramas (`flow_transition`);
- en el Portal vive en **Flujos** (`/{org}/{proyecto}/flows`), con su lienzo, «Probar como…», las pestañas Pruebas y Versiones, y «Siguiente iteración» (`notes`);
- `properties.steps` y `alternatives` del nodo son una **proyección** que escribe `flow_save`. `knowledge_update` no los cambia («Los pasos de este flujo se editan en el canvas o con flow_save, no con knowledge_update.»).

## 1. El modelo

**Paso** (`steps[]`): `{key, kind, title, detail?, actor?, screen?, action?, integration?, position?}`.

| `kind` | Qué es |
|---|---|
| `start` | Lo que dispara el flujo (sale del `trigger`) |
| `step` | Algo que hace una persona o el sistema |
| `decision` | Un punto donde el camino se divide. **Nunca lleva `screen`** |
| `end` | Un resultado (sale del `outcome`, o de cada rama que termina) |

- `key`: id estable dentro del flujo (`[A-Za-z0-9_-]`, ≤64). Los pasos que no mandas **se borran**.
- `actor`, `screen`, `action` e `integration` son refs (`kind/slug`, uuid o short id) a nodos del **proyecto o de la organización** del kind correcto. Uno que no existe o de otro kind da `invalid_input` con `cause.code: FLOW_STEP_REF` y la ruta (`steps.3.screen`).
- `detail` es el resultado esperado del paso: es lo que ve quien prueba.

**Transición** (`transitions[]`): `{from, to, kind, label?}`.
- `next` (por omisión): el camino principal.
- `branch`: una salida etiquetada de una decisión («Aprobada», «Rechazada»).
- `alternative`: «si algo sale distinto», etiquetada.
- `branch` y `alternative` exigen `label`. No hay transiciones de un paso a sí mismo ni repetidas.

Límites: 120 pasos y 240 transiciones. `layoutDirection`: `TB` (de arriba abajo) es el valor **por omisión**; manda `LR` solo si la persona lo pide.

**Nodos que el flujo referencia** (se crean con `knowledge_create`, skill `knowledge`; plantillas en `${CLAUDE_PLUGIN_ROOT}/skills/knowledge/references/kinds.md`):

| Kind | Para | Obligatorios |
|---|---|---|
| `actor` | Quién hace el paso | ver skill `screens` |
| `screen` | Dónde pasa (v3) | ver skill `screens` |
| `action` | Lo que la persona hace en la pantalla, o lo que el sistema hace solo | `trigger` (`button`, `form`, `link`, `automatic`), `effect` |
| `integration` | El servicio que corre el paso (Stripe, un webhook, un IdP) | `provider`, `state` (`described`, `simulated`, `real`), `operation`. Si es `simulated`, `sampleResponse` (JSON ≤16 KB) es obligatoria; `sampleCases` (`{case, response}`) agrega los casos que elige quien prueba |

Aristas que deriva `flow_save` de los pasos (`fromSection: "flow_steps"`): actor `performs` flujo, flujo `uses` pantalla y acción, y flujo `triggers` integración. Una acción que dispara el flujo se enlaza a mano: `knowledge_link` acción `triggers` flujo.

## 2. Tools

| Tool | Qué hace | Quién |
|---|---|---|
| `flow_list` | Flujos del proyecto: ref, título, versión, pasos, roles y la última prueba | Staff y cliente (solo los `client`) |
| `flow_get {ref}` | Disparador, resultado, pasos en orden con sus refs, transiciones, `revision`, versión y las últimas pruebas, con el resultado de cada paso. En hosts con MCP Apps se dibuja como vista (`Flow`) | Staff y cliente |
| `flow_create {title, trigger?, outcome?, summary?, visibility?, graph?, sources, idempotencyKey?}` | Crea el flujo. Sin `graph` nace con un inicio (el disparador) y un fin (el resultado). `sources` es obligatorio | Staff |
| `flow_save {ref, graph \| mermaid, expectedRevision, idempotencyKey, changeSummary?}` | **Reemplaza** el grafo completo | Staff |
| `flow_version_bump {ref, label}` | v1 → v2… con etiqueta («Integraciones simuladas»). No cambia la `revision` | Staff |
| `flow_run_start {ref, actor?, mode}` | Inicia una prueba. Devuelve su `ref` | Staff y cliente |
| `flow_run_step {run, stepKey, result, note?, branchLabel?, integrationResponse?}` | Registra un paso | Quien inició la prueba |
| `flow_run_finish {run, status, stoppedAtKey?, notes?}` | Cierra la prueba | Quien la inició |
| `flow_run_list {ref, limit?}` / `flow_run_get {run}` | Historial y detalle de pruebas | Staff y cliente (el cliente ve las de su organización, no las del equipo de Pai) |

Todas reciben `organizationId` y `projectId`. `ref` del flujo: uuid, short id, `flow/<slug>` o slug.

### `flow_save`: CAS e idempotencia

1. `flow_get` y toma `revision`.
2. Compón el grafo **completo** a partir de lo leído: lo que no mandes se borra.
3. `flow_save` con `expectedRevision` = esa revisión e `idempotencyKey` estable (`flow-<proyecto>-<slug>-<n>`). Si reintentas, usa la misma clave.
4. `CONFLICT`: alguien guardó antes (el lienzo es colaborativo y en vivo). Relee, integra y reintenta una vez.
5. Revisa `warnings` y la respuesta: trae el flujo con su nueva `revision`.

**Mermaid** en lugar de `graph`: `{…}` es decisión, `([…])` inicio o fin, `-->|condición|` desde una decisión es una rama y `-. texto .->` una alternativa. Sirve para un borrador. Las refs a actor, pantalla, acción e integración solo van con `graph`.

## 3. Antes de crear: reusa lo que ya existe

En Unicef se crearon actores y acciones que ya estaban en el proyecto. Para no repetirlo:

1. `flow_list` y `knowledge_library {projectId, kinds: ["flow","actor","screen","action","integration"]}` (recorre `offset` hasta `total`). Busca también en la organización: un flujo puede referenciar sus actores.
2. `knowledge_search` por nombre, en español y en inglés.
3. **Flujos migrados:** los flujos v1 (pasos en `properties`) ya tienen entidad (`flows:backfill`) o la ganan al abrirlos. **Corrígelos con `flow_save`; no crees uno nuevo.**
4. Si dos nodos parecen el mismo (dos «Cliente», dos «Pagar»), no crees un tercero: usa uno y anota el duplicado para que lo decida una persona.

## 4. Requisitos para que se pueda probar

«Probar como…» arranca en el paso `start` y sigue las transiciones. Antes de dar un flujo por terminado, revisa este **checklist** con `flow_get`:

- [ ] **Un solo `start`**. Sin él, «Empezar» queda deshabilitado (era el bloqueante de los 24 flujos migrados de develop).
- [ ] **Al menos un `end`**, y cada camino termina en uno.
- [ ] **Todos los pasos se alcanzan** desde el inicio.
- [ ] **Cada decisión tiene 2 o más ramas**, todas con `label`. Las alternativas que solo están en el texto o en `notes` («si la tarjeta es rechazada…») pasan a ser ramas.
- [ ] **Actor en cada paso**, decisiones y fines incluidos: alimenta el selector de rol y atenúa los pasos de otros roles.
- [ ] **Pantalla y acción ligadas cuando existen** (nunca pantalla en una decisión). Para que el paso se vea al probarlo, la pantalla lleva `prototype: {pageId, blockId?}` hacia su page `pantallas/<producto>/…` con un bloque **`view`**; un bloque `html` no sirve como prototipo (skill `screens`).
- [ ] **Integraciones ligadas.** Si se van a probar, `state: simulated` con `sampleResponse` y, si hay variantes, `sampleCases` (éxito, reembolso, disputa…).
- [ ] `detail` en cada paso: es el resultado esperado que lee quien prueba.

`${CLAUDE_PLUGIN_ROOT}/tools/validate-examples.ts` aplica este checklist a los ejemplos de `flow_save`.

**No inventes reglas de negocio.** Si el texto no dice quién decide, cuál es la rama o qué responde la integración, no lo completes por tu cuenta: anótalo en `notes` del flujo («Siguiente iteración») o como `question` (skill `knowledge`) y díselo a la persona. Ejemplos de develop que quedaron para decidir: un rol de validador que no existe como nodo, un paso que mezcla tres roles, o dos fines del mismo flujo que se contradicen.

## 5. Probarlo con `flow_run_*`

1. `flow_run_start {ref, actor: "actor/<rol>", mode}`.
   - `mode: "sample"` (datos de ejemplo) o `"simulated"` (las respuestas de ejemplo de las integraciones). `"real"` todavía no: `FLOW_RUN_REAL_DISABLED`.
   - `actor` es un nodo `actor` del flujo; otro kind da `FLOW_RUN_ACTOR`. Un flujo archivado o reemplazado no se prueba (`FLOW_RUN_FLOW_CLOSED`).
2. Recorre desde `start` y registra cada paso con `flow_run_step`. En un paso con pantalla, «Probar como…» muestra su prototipo (el bloque `view` de su `prototype`) con las acciones que la pantalla ofrece como zonas clicables; sin prototipo, solo la descripción:
   - `passed`: hace lo que dice `detail`;
   - `noted`: pasa con una observación. Úsalo cuando **falta la integración** o la pantalla y el paso solo se revisó con su descripción, y dilo en `note`;
   - `failed`: no se cumple. Ahí se detiene la prueba;
   - `skipped`: lo hace otro rol, o no aplica a la rama.
   - En una decisión, `branchLabel` = la etiqueta de la rama elegida. En un paso con integración simulada, `integrationResponse` = la respuesta (o el caso) que se mostró.
3. Cierra con `flow_run_finish`: `passed`, `passed_with_notes` (si hubo `noted`), `failed` (con `stoppedAtKey`, o toma el último paso fallido; sin ninguno da `FLOW_RUN_STOPPED_AT`) o `abandoned`.
4. Para cubrir ramas, haz **una prueba por rama** importante (el camino feliz y cada fin), no una sola que lo mezcle todo.

Solo quien inició la prueba la continúa (`FLOW_RUN_NOT_RUNNER`). Una prueba cerrada no se edita (`FLOW_RUN_FINISHED`). Un `stepKey` que no existe da `FLOW_RUN_STEP_KEY`. Las pruebas son nodos `flow_run` (rel `tests`) que crea la prueba; nunca uses `knowledge_create kind=flow_run`.

## 6. El orden con el cliente

Un agente **no edita lo que el cliente ya ve** (`CLIENT_VISIBLE_REQUIRES_PERSON`). El agente del staff en el MCP corp sí puede cambiar solo la visibilidad, y guardar el grafo de un flujo `client` con `flow_save`. Por eso:

1. Crea **todo `internal`**: actores, pantallas, acciones, integraciones y el flujo.
2. Arma el grafo con `flow_save` y pásale el checklist (§4). Pruébalo (§5).
3. **Al final**, con el visto bueno de la persona, `knowledge_update {ref, expectedRevision, visibility: "client", changeSummary}`, uno por nodo (relee cada uno con `knowledge_get`). Solo `visibility`, sin otros campos.
4. Para corregir después un nodo que ya es `client`, crea una propuesta o pídeselo a una persona. **No lo rodees** volviéndolo `internal`, editándolo y publicándolo otra vez.

El cliente ve en Flujos solo los flujos `client`. Una ref a un nodo que no ve sale como «Interno», sin ref, y `sampleResponse` solo se muestra si la integración es `client`.

## 7. Mostrarlo

- En la conversación: `flow_get` se dibuja solo en hosts con MCP Apps. Si no, `view_render` con el componente `Flow` (skill `views`).
- En una page: bloque `{id, type: "flow", node, title?, height?}`, donde `node` es el **uuid** del flujo del mismo proyecto. Dibuja su lienzo en solo lectura con «Abrir» (skill `resources`).

## 8. Ejemplos

Validados contra los contratos y contra `flow_get` de develop del 2026-10-15: pasos, refs, transiciones `next`, ramas y textos coinciden; ninguno trae `layoutDirection` (TB). El grafo de `flow_save` reproduce el flujo tal como está (Unicef r6, Morelos r2), así que guardarlo no cambia nada; parte de él para corregir.

- `${CLAUDE_PLUGIN_ROOT}/skills/flows/examples/unicef-donation.json`: **Pago con donativo a Unicef** (`flow/donation-payment`, Checkout Merchants). Busca lo que existe, `flow_get`, `flow_save` con 22 pasos y las ramas «Puede recibir», «Unicef no puede recibir», «Aprobada», «Rechazada», «Sin cambios», «Reembolso parcial», «Disputa», «Ganada» y «Perdida», una prueba `simulated` como Cliente con la integración de Stripe y, al final, la visibilidad `client`.
- `${CLAUDE_PLUGIN_ROOT}/skills/flows/examples/morelos-entry.json`: **Recorrido de entrada** (`flow/flow-pf-entry`, Portal Funcionario). Decisiones «¿El IdP autentica?» y «¿Cuántas membresías tiene?» (Ninguna, Una, Varias) y una prueba `sample` donde el paso de Llave Morelos queda `noted` porque la integración no existe todavía.

Fragmento del grafo de Unicef:

```json
{
  "steps": [
    {"key": "start", "kind": "start", "title": "El cliente elige un donativo y pulsa «Pagar»", "actor": "actor/customer"},
    {"key": "c1", "kind": "decision", "title": "¿El banco aprueba la tarjeta?", "actor": "actor/customer"},
    {"key": "s6", "kind": "step", "title": "Cobra y transfiere el donativo a Unicef", "actor": "actor/stripe",
     "integration": "integration/stripe-payment-intent-transfer-data"},
    {"key": "c2", "kind": "end", "title": "Tarjeta rechazada", "actor": "actor/customer"}
  ],
  "transitions": [
    {"from": "c1", "to": "s6", "kind": "branch", "label": "Aprobada"},
    {"from": "c1", "to": "c2", "kind": "branch", "label": "Rechazada"}
  ]
}
```

## Qué no hacer

- **No** escribas los pasos en `properties.steps` con `knowledge_create` o `knowledge_update`: usa `flow_save`.
- **No** mandes un grafo parcial a `flow_save`: borra los pasos que faltan.
- **No** dejes las alternativas en `notes` cuando el texto dice claramente cuál es la rama: modélalas como `branch`.
- **No** inventes actores, decisiones ni respuestas de integración para que el flujo «pase» el checklist: lo que no está claro se anota.
- **No** publiques (`visibility: client`) antes de terminar el grafo y probarlo.
