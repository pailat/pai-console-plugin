---
name: screens
description: Documenta las pantallas, flujos y actores de un producto en el Conocimiento de un proyecto de Pai Console (nodos screen, flow y actor). Úsalo cuando pidan inventario de pantallas, mapa de navegación, flujos de usuario, journeys o qué hace cada pantalla y quién la usa.
argument-hint: "[proyecto] [producto, ruta o flujo a documentar]"
---

# Pantallas y flujos en Pai: `screen`, `flow` y `actor`

Lee antes el skill `pai-console`.

## Qué es cada nodo

| Nodo | Qué representa | Obligatorios |
|---|---|---|
| `actor` | Quién usa el producto | `actorType` (`person`, `role`, `system` o `agent`), `description` (10–1000), `goals` (≥1). Opcionales: `portalRole`, `permissions` |
| `screen` | Una pantalla: ruta, propósito, quién la usa, sus estados, lo que muestra y lo que permite | `route`, `purpose` (15–1500), `actors` (≥1), `states` (≥2), `content` (≥1 fila `{block, data?, source?}`), `actions` (≥1 fila `{action, effect?, rule?}`) |
| `flow` | Un recorrido, de un disparador a un resultado | `trigger`, `outcome`, `summary` (15–1500), `steps` (≥2, numerados `n` = 1..k sin huecos, con `{n, actor, action, screen?, result, rule?}`) |

Las referencias de `screen` crean aristas:
- `actors` → el actor `performs` la pantalla;
- `rules` → la regla o restricción `constrains` la pantalla;
- `uses` → una entidad o un componente;
- `navigatesTo` → otra pantalla (`navigates_to`).

En un `flow`, `actor`, `screen` y `rule` de cada paso son referencias de lectura: **no crean aristas**. Si el flujo debe aparecer en el grafo del actor, enlázalo con `knowledge_link` (`performs`, de `actor` a `flow`).

## Orden

1. **Busca:** `knowledge_search` con `kinds:["actor","screen","flow"]`, por ruta y por nombre. Reutiliza los actores que ya existan (los comparten C4 y las pantallas).
2. **Actores** que falten.
3. **Pantallas destino primero:** la pantalla a la que se navega va antes que la que navega a ella. Si no, `navigatesTo` da un warning y no crea la arista.
4. **Pantallas de origen,** con `navigatesTo`. Si hay ERD o C4, liga cada pantalla en `uses` con sus entidades o su contenedor web.
5. **Flujos,** referenciando actores y pantallas que ya existen.
6. **Verifica** con `knowledge_get` las aristas `performs`, `navigates_to` y `uses`, y revisa los `warnings` de cada respuesta.

Ejemplo validado: `examples/checkout.json`. Son dos pantallas con navegación entre ellas y un flujo de tres pasos con una alternativa. Reutiliza `actor/shopper` y las entidades del ejemplo de ERD.

## Criterio

- **`route`** es la ruta real, en inglés: `/orders/[orderId]`, no «Detalle de pedido». Los parámetros van entre corchetes, como en Next.js.
- **`states`** enumera lo que la persona ve, no los estados del código: «Cargando», «Vacío», «Error», «Listo». Si una pantalla solo tiene un estado, probablemente es un bloque de otra pantalla.
- **`content`** son bloques de la pantalla. En `source` va de dónde salen sus datos (`entity/<slug>` o el nombre de la API).
- **`actions`** son lo que la persona puede hacer y su efecto. Si una regla de negocio limita la acción, ponla en `rule` (`business_rule/<slug>`).
- **`wireframe`** (opcional): `{description, url?}` (Figma) o `{description, pageId?}` (una page de Recursos con la imagen).
- Un **flujo** cuenta un recorrido completo con resultado observable. No es un paso suelto ni una lista de pantallas. Los caminos de error van en `alternatives`.

## Nombres

- Slugs en inglés y kebab-case: `screen/checkout`, `flow/place-order`, `actor/shopper`.
- Títulos en español.
- `idempotencyKey`: `kn-<proyecto>-screen-<slug>`.

## Qué no hacer

- **No** crees una pantalla por estado ni por modal menor: los estados van en `states`.
- **No** inventes rutas: si no las conoces, pregúntalas o léelas del repositorio (y cítalo en `sources`).
- **No** pongas un diagrama Mermaid en `properties`: el diagrama del flujo se genera desde los pasos.
- **No** dejes `actors` vacío: una pantalla sin quien la use no se acepta.
