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
| `action` | Lo que la persona hace en una pantalla (botón, formulario, enlace) o lo que el sistema hace solo. **Una acción se reutiliza entre pantallas** | `trigger` (`button`, `form`, `link`, `automatic`), `effect`. Opcionales: `inputs` (`{field, type, required}`), `outcome` |
| `screen` (v3) | Una pantalla: ruta, propósito, quién la usa, sus estados, lo que muestra y las acciones que ofrece | `route`, `purpose` (15–1500), `actors` (≥1), `states` (≥2), `content` (≥1 fila `{block, data?, source?}`). Opcionales: `actions`, `rules`, `uses`, `navigatesTo`, `view`/`views` |

Plantillas completas: `${CLAUDE_PLUGIN_ROOT}/skills/knowledge/references/kinds.md`.

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

## Orden

1. **Busca:** `knowledge_library {projectId, kinds:["actor","screen","action","flow"]}` para el inventario (recorre `offset`) y `knowledge_search` por ruta y por nombre. **Reutiliza** los actores y las acciones que ya existan: los comparten C4, las pantallas y los flujos. Si encuentras dos que parecen la misma acción, no crees una tercera: usa una y anota el duplicado.
2. **Actores** que falten.
3. **Acciones** que falten (`kn-<proyecto>-action-<slug>`).
4. **Pantallas destino primero:** la pantalla a la que se navega va antes que la que navega a ella. Si no, `navigatesTo` da un warning y no crea la arista. Lo mismo para `actions` y `source`: el nodo citado debe existir.
5. **Pantallas de origen,** con `navigatesTo`. Si hay ERD o C4, liga cada pantalla en `uses` con sus entidades o su contenedor web, y conecta `content[].source`.
6. **Aristas de las acciones** con `knowledge_link` (`navigates_to`, `performs`, `uses`, `constrains`, `triggers`).
7. **Flujos:** con el skill `flows` (`flow_create` / `flow_save`). **No escribas los pasos a mano** en `properties.steps` de un nodo `flow`: el flujo v1 de pasos en `properties` ya no se escribe así, ahora son una proyección de `flow_save`.
8. **Verifica** con `knowledge_get` las aristas `performs`, `offers`, `navigates_to` y `uses`, revisa los `warnings` de cada respuesta y corre `knowledge_audit` para ver si quedó alguna «fuente sin conectar».

Ejemplo validado: `${CLAUDE_PLUGIN_ROOT}/skills/screens/examples/checkout.json`. Son tres acciones y dos pantallas v3 con navegación entre ellas y fuentes conectadas. Reutiliza `actor/shopper` y las entidades del ejemplo de ERD. El flujo de esas pantallas está en el skill `flows`.

## Criterio

- **`route`** es la ruta real, en inglés: `/orders/[orderId]`, no «Detalle de pedido». Los parámetros van entre corchetes, como en Next.js.
- **`states`** enumera lo que la persona ve, no los estados del código: «Cargando», «Vacío», «Error», «Listo». Si una pantalla solo tiene un estado, probablemente es un bloque de otra pantalla.
- **`content`** son bloques de la pantalla, con `source: {ref: "entity/<slug>"}` (o el `data_model`, la acción, la integración o el flujo de donde salen sus datos).
- **Una acción** se nombra por lo que hace la persona («Pagar», «Editar carrito»), con su `effect` y, si pide datos, sus `inputs`. Si una regla de negocio la limita, enlázala con `constrains`.
- **`view` / `views`** (opcional): la pantalla dibujada como `pai-view@1` (skill `views`), una por estado en `views`.

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
