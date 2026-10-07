---
name: c4
description: Modela la arquitectura C4 de un sistema en el Conocimiento de un proyecto de Pai Console. Usa nodos component por nivel (context, container, component, code) y nodos actor para las personas; las relaciones llevan descripción y tecnología. Úsalo cuando pidan arquitectura, C4, diagrama de contexto o de contenedores, componentes o el mapa de un sistema.
argument-hint: "[proyecto] [sistema o repositorio a documentar]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# C4 en Pai: `component` por nivel + `actor`

Lee antes el skill `pai-console`.

## El modelo

- **Cada elemento C4 es un nodo `component`** con su `c4Level` y su `c4Type`.
- **Las personas son nodos `actor`**, nunca un `component` de tipo `Person`.
- La **jerarquía** se declara con `parent`: el elemento del nivel inmediatamente superior lo contiene (`contains`).
- Las **interacciones** se declaran con `relationships`: el servidor crea aristas `uses` entre componentes y `performs` desde un actor.
- El diagrama se genera solo, por nivel, con navegación entre los cuatro niveles.

| `c4Level` | `c4Type` permitidos | `technology` |
|---|---|---|
| `context` | `System`, `System_Ext` | opcional |
| `container` | `Container`, `ContainerDb`, `ContainerQueue`, `System_Ext` | **obligatoria** |
| `component` | `Component`, `ContainerDb`, `System_Ext` | **obligatoria** |
| `code` | `Code` (+ `codeKind`: class, interface, enum, entity o function) | opcional |

## Orden

1. **Descubre** el proyecto y **busca lo que ya existe**:
   - **inventario:** `knowledge_library {projectId, kinds:["component","actor"]}`, recorriendo `offset` hasta `total`;
   - **de la organización:** el mismo `knowledge_library` con `projectId: "organization"`. Los modelos y sistemas compartidos del cliente pueden vivir ahí: enlázalos por uuid en vez de recrearlos;
   - **por tema:** `knowledge_search` con esos kinds y el nombre del sistema.

   Si el sistema ya está, **agrega debajo**; no lo dupliques.
2. **Actores primero:** `actor` con `actorType` (`person`, `role`, `system` o `agent`), `description` (10–1000) y `goals` (≥1). Reutiliza los actores que ya existan: los comparten las pantallas y los flujos.
3. **Nivel context:** el `System` y los `System_Ext` (proveedores y sistemas del cliente).
4. **Nivel container,** con `parent: ["component/<sistema>"]`. Las bases de datos son `ContainerDb`, con `dataModels: ["data_model/<slug>"]` para ligarlas al ERD (skill `erd`).
5. **Nivel component** (solo donde aporte), con `parent: ["component/<contenedor>"]` y `stereotype` cuando aplique.
6. **Nivel code:** casi nunca. Solo si la persona lo pide o el elemento es central.
7. **Siempre crea primero el destino de una relación o de un `parent`.** Si el destino no existe, la escritura no falla: devuelve un warning y no crea la arista. Si pasó, vuelve a guardar el nodo cuando el destino exista.
8. **Verifica con `knowledge_view {view:"c4", scope:"component/<sistema>", level, format:"json"}`**, nivel por nivel (`context`, luego `container`…). Es la misma vista que dibuja el Portal.
   - Los elementos del nivel están, con su `c4Type` y su `technology`. Las personas aparecen como actores.
   - Las relaciones llevan la `description` y la `technology` que declaraste.
   - El árbol (`tree`) cuelga cada elemento de su padre.
9. **Entrega** a la persona:
   - **el diagrama dibujado:** `view_render` con un `C4Diagram` que recibe la respuesta de `knowledge_view` tal cual (skill `views`, «Diagramas de Conocimiento»);
   - las citas `kb:`;
   - el Mermaid (`format:"mermaid"`) si lo pide;
   - el enlace del Portal: el `url` de la vista (ya trae `?level=`) con el host del Portal delante (`https://app.pai.lat` en producción; en staging, el Portal de staging).

Ejemplo completo y validado: `${CLAUDE_PLUGIN_ROOT}/skills/c4/examples/shop-c4.json`. Incluye un actor, un sistema, un sistema externo, tres contenedores (uno de ellos BD ligada al ERD), un repository y un controller.

## Relaciones (`relationships`, ≤30 por nodo)

```json
{ "to": "component/shop-api", "direction": "out", "description": "Consulta y crea pedidos", "technology": "HTTPS/JSON" }
```

| Campo | Contenido |
|---|---|
| `description` | **Es la etiqueta de la flecha** (3–120 caracteres). Un verbo y su objeto: «Cobra los pedidos». **No existe `label`.** |
| `technology` | Protocolo o mecanismo (≤60): `HTTPS/JSON`, `SQL/TLS`, `AMQP`, `gRPC`, `Webhook`. |
| `direction: "out"` | Este elemento usa a `to`. |
| `direction: "in"` | `to` usa a este elemento. **Con un actor siempre va `in`**, porque la persona inicia la relación. |

El par `direction:to` es único dentro de un nodo.

Declara cada relación **una sola vez**, en el nodo que la inicia (`out`), salvo las de actores, que van con `in` en el elemento que usan.

## Estereotipos (solo en el nivel component)

| `stereotype` | Lleva | Exige |
|---|---|---|
| `controller` | `httpRoutes[{method, path, handler?, description?}]`, `methods` | — |
| `service`, `interface` | `methods[{name, parameters?, returns?, visibility?, description?}]` | — |
| `repository` | `methods`, `dataOperations` (create, read, update, delete, list, count) | `entity: ["entity/<slug>"]`, que es el puente al ERD |
| `module` | `exports` | — |
| `component` | por defecto | — |

En el nivel code, `codeKind` decide qué lleva:
- `class`: `attributes`, `methods` y `httpRoutes`;
- `interface` y `function`: `methods`;
- `enum`: `enumValues`, obligatorio;
- `entity`: `attributes` y `entity`.

## Nombres

- Slugs en inglés y kebab-case: `shop-system`, `shop-api`, `orders-controller`.
- Títulos en español.
- `technology` con producto y versión mayor cuando importa: «Next.js 16», «PostgreSQL 16».
- `responsibility` (15–1000 caracteres): qué hace y qué no, en una o dos frases.

## Qué no hacer

- **No** uses `c4Type: "Person"`: es un `actor`.
- **No** saltes niveles con `parent`: un container cuelga de un context y un component de un container. Si no, da `C4_LEVEL`. Un nodo tiene **un solo** padre (`ALREADY_CONTAINED`).
- **No** dejes un container o component sin `technology`.
- **No** escribas `label`, ni Mermaid en `properties` (`MERMAID_NOT_ALLOWED`).
- **No** pongas `stereotype` fuera del nivel component, ni `httpRoutes` fuera de un controller o una class.
- **No** crees aristas `uses`, `performs` o `contains` a mano: salen de `relationships` y de `parent`.
- **No** modeles cada clase: el C4 sirve para entender el sistema, no para copiar el código.

## Cambios posteriores

1. `knowledge_get` del nodo.
2. `knowledge_update` con **todas** las `properties` (las `relationships` completas) y `expectedRevision`.

Si quitas una fila de `relationships`, su arista desaparece. Para retirar un elemento usa `knowledge_archive` con motivo.
