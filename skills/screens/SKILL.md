---
name: screens
description: Documenta las pantallas, acciones y actores de un producto en el Conocimiento de un proyecto de Pai Console (nodos screen v3, action y actor; los flujos van con el skill flows). Úsalo cuando pidan inventario de pantallas, mapa de navegación, qué hace cada pantalla y quién la usa, qué acciones ofrece, o conectar una pantalla con sus datos.
argument-hint: "[proyecto] [producto, ruta o pantalla a documentar]"
compatibility: "Pai 0.2.5+ (MCP corp; screen v3 desde d65d611ac)"
---

# Pantallas, acciones y actores en Pai: `screen`, `action` y `actor`

Lee antes el skill `pai-console`. Los **flujos** (recorridos con pasos, ramas y pruebas) tienen su propio skill: `flows`.

## Qué es cada nodo

| Nodo | Qué representa | Obligatorios |
|---|---|---|
| `actor` | Quién usa el producto | `actorType` (`person`, `role`, `system` o `agent`), `description` (10–1000), `goals` (≥1). Opcionales: `portalRole`, `permissions` |
| `action` | Lo que la persona hace en una pantalla (botón, formulario, enlace) o lo que el sistema hace solo. **Una acción se reutiliza entre pantallas** | `trigger` (`button`, `form`, `link`, `automatic`), `effect`. Opcionales: `inputs` (`{field, type, required}`), `outcome`, `hotspot` |
| `screen` (v3) | Una pantalla: ruta, propósito, quién la usa, sus estados, lo que muestra y las acciones que ofrece | `route`, `purpose` (15–1500), `actors` (≥1), `states` (≥2), `content` (≥1 fila `{block, data?, source?}`). Opcionales: `actions`, `rules`, `uses`, `navigatesTo`, `prototype`, `view`/`views` |

Plantillas completas: `../knowledge/references/kinds.md`.

### La pantalla v3 está conectada

- **`actions` son refs a nodos `action`** (rel `offers`, pantalla → acción). Ya no son filas de texto `{action, effect, rule}`: el servidor las rechaza con «Las acciones de una pantalla son nodos action: crea la acción (o corre screens:actions-to-nodes) y nómbrala por su ref.». `offers` no fija contenedor, así que la misma acción puede estar en varias pantallas.
- **`content[].source` es `{ref}`**: el nodo del que salen los datos del bloque (`entity`, `data_model`, `action`, `integration` o `flow`). Crea la arista `uses` desde la sección `content`. El texto libre de v2 todavía se acepta, pero `knowledge_audit` lo lista como **«fuente sin conectar»** (`unconnectedSources`): conéctala con `{ref}` cuando el nodo exista.
- Una pantalla v2 se sigue leyendo; en su siguiente edición (o con el script `screens:actions-to-nodes` del servidor) pasa a v3. Para editar una v2, crea primero sus acciones y cambia `actions` a refs.

Aristas que crean las refs de `screen`:
- `actors` → el actor `performs` la pantalla;
- `actions` → la pantalla `offers` la acción;
- `rules` → la regla o restricción `constrains` la pantalla;
- `uses` → una entidad o un componente;
- `navigatesTo` → otra pantalla (`navigates_to`);
- `content[].source {ref}` → `uses` (desde `content`).

Lo de una acción que no está en su plantilla se enlaza con `knowledge_link`:
- a dónde lleva: acción `navigates_to` pantalla;
- quién la ejecuta: actor `performs` acción;
- qué datos toca: acción `uses` entidad o modelo de datos (`properties.mode`: `create`, `update` o `read`);
- qué regla la limita: `business_rule`/`constraint` `constrains` acción;
- qué dispara: acción `triggers` flujo o integración («Pagar» corre Stripe).

### El prototipo de la pantalla: siempre un bloque `view`

`properties.prototype = {pageId, blockId?}` apunta a la page de Recursos que dibuja la pantalla, en `pantallas/<producto>/…`, y a su bloque **`view`** (vista de Pai, `pai-view@1`, skill `views`).
- `pageId` es el uuid de una page **del mismo proyecto**. Sin `blockId`, el prototipo es el primer bloque `view` de la page; con él, ese bloque. Cada bloque `view` de la page es un estado de la pantalla.
- **Un bloque `html` no sirve como prototipo** (decisión del owner): un mockup o prototipo HTML sigue siendo un recurso válido, pero no se liga como prototipo de una pantalla. Si la pantalla solo existe en HTML, rehazla como vista con el skill `views`.
- Es una referencia suave: no crea arista ni cambia el `pageId` del nodo. Como no es un campo del formulario, `kinds.md` no lista `prototype` (ni el `hotspot` de la acción), pero el servidor los acepta en `properties`.
- «Probar como…» dibuja el prototipo en el paso del flujo que pasa por la pantalla, con las acciones que ofrece como zonas clicables (skill `flows`). Sin prototipo, muestra la descripción.
- Errores al escribir la pantalla (`BAD_REQUEST` con `cause.code`, y `cause.pageId`). Solo se revisa un `prototype` nuevo o cambiado:
  - `PROTOTYPE_PAGE_NOT_IN_PROJECT`: la page no existe en el proyecto de la pantalla (o el nodo no es de un proyecto);
  - `PROTOTYPE_BLOCK_NOT_FOUND`: la page no tiene ese `blockId`;
  - `PROTOTYPE_NOT_VIEW`: el `blockId` es un bloque `html`, o la page no tiene ningún bloque `view`.
- **La zona clicable de una acción** es el elemento del prototipo cuyo texto visible es el título de la acción. Si no coincide, fíjalo en la acción con `hotspot: {elementId?, text?}` (al menos uno): el `elementId` de un elemento del spec `view`, o su texto visible.
- Un cliente solo ve el prototipo si la page es `client` del mismo proyecto. Si no, la pantalla le llega sin `prototype`.

## Orden

1. **Busca:** `knowledge_library {projectId, kinds:["actor","screen","action","flow"]}` para el inventario (recorre `offset`) y `knowledge_search` por ruta y por nombre. **Reutiliza** los actores y las acciones que ya existan: los comparten C4, las pantallas y los flujos. Si encuentras dos que parecen la misma acción, no crees una tercera: usa una y anota el duplicado.
2. **Actores** que falten.
3. **Acciones** que falten (`kn-<proyecto>-action-<slug>`).
4. **Pantallas destino primero:** la pantalla a la que se navega va antes que la que navega a ella. Si no, `navigatesTo` da un warning y no crea la arista. Lo mismo para `actions` y `source`: el nodo citado debe existir.
5. **Prototipo:** si la pantalla se va a ver o a probar, crea primero la page `pantallas/<producto>/<pantalla>` con su bloque `view` (skill `views`) y pon `prototype: {pageId, blockId?}` en la pantalla.
6. **Pantallas de origen,** con `navigatesTo`. Si hay ERD o C4, liga cada pantalla en `uses` con sus entidades o su contenedor web, y conecta `content[].source`.
7. **Aristas de las acciones** con `knowledge_link` (`navigates_to`, `performs`, `uses`, `constrains`, `triggers`).
8. **Flujos:** con el skill `flows` (`flow_create` / `flow_save`). **No escribas los pasos a mano** en `properties.steps` de un nodo `flow`: el flujo v1 de pasos en `properties` ya no se escribe así, ahora son una proyección de `flow_save`.
9. **Verifica** con `knowledge_get` las aristas `performs`, `offers`, `navigates_to` y `uses`, revisa los `warnings` de cada respuesta y corre `knowledge_audit` para ver si quedó alguna «fuente sin conectar».

Ejemplo validado: `examples/checkout.json`. Son tres acciones y dos pantallas v3 con navegación entre ellas y fuentes conectadas. Reutiliza `actor/shopper` y las entidades del ejemplo de ERD. El flujo de esas pantallas está en el skill `flows`.

## Criterio

- **`route`** es la ruta real, en inglés: `/orders/[orderId]`, no «Detalle de pedido». Los parámetros van entre corchetes, como en Next.js.
- **`states`** enumera lo que la persona ve, no los estados del código: «Cargando», «Vacío», «Error», «Listo». Si una pantalla solo tiene un estado, probablemente es un bloque de otra pantalla.
- **`content`** son bloques de la pantalla, con `source: {ref: "entity/<slug>"}` (o el `data_model`, la acción, la integración o el flujo de donde salen sus datos).
- **Una acción** se nombra por lo que hace la persona («Pagar», «Editar carrito»), con su `effect` y, si pide datos, sus `inputs`. Si una regla de negocio la limita, enlázala con `constrains`.
- **`view` / `views`** (opcional): la pantalla dibujada como `pai-view@1` dentro del nodo, una por estado en `views`. Lo que dibuja «Probar como…» es el **`prototype`** (la page con su bloque `view`).

## Nombres

- Slugs en inglés y kebab-case: `screen/checkout`, `action/checkout-pay`, `actor/shopper`.
- Títulos en español.
- `idempotencyKey`: `kn-<proyecto>-screen-<slug>` y `kn-<proyecto>-action-<slug>`.

## Qué no hacer

- **No** escribas `actions` como filas de texto: crea los nodos `action` y cítalos.
- **No** dupliques una acción por pantalla: la misma acción se ofrece en varias (`offers`).
- **No** crees una pantalla por estado ni por modal menor: los estados van en `states`.
- **No** inventes rutas: si no las conoces, pregúntalas o léelas del repositorio (y cítalo en `sources`).
- **No** escribas los pasos de un flujo en `properties`: usa el skill `flows`.
- **No** dejes `actors` vacío: una pantalla sin quien la use no se acepta.
- **No** ligues un bloque `html` como `prototype`: el prototipo de una pantalla es siempre un bloque `view`.
