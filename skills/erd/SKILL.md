---
name: erd
description: Modela un ERD (modelo de datos) en el Conocimiento de un proyecto de Pai Console con nodos data_model y entity. Las columnas son tipadas y las relaciones se derivan de las claves foráneas. Úsalo cuando pidan un modelo de datos, un ERD, tablas, entidades o un esquema de base de datos, o pasar un schema.sql o migraciones a Pai.
argument-hint: "[proyecto] [descripción del dominio | ruta a schema.sql o migraciones]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# ERD en Pai: `data_model` + `entity`

Lee antes el skill `pai-console` (entorno, descubrimiento, buscar antes de crear, CAS).

## El modelo en una frase

Un **`data_model`** agrupa **`entity`** (tablas). **Una entidad son sus columnas.** Las relaciones **no se escriben**: salen de las columnas con clave foránea. El servidor deriva la cardinalidad y crea las aristas `relates_to`. El diagrama se genera solo.

## Orden

1. **Descubre** organización y proyecto (`pai-console` §1).
2. **Busca lo que ya existe:**
   - **inventario:** `knowledge_library {projectId, kinds:["data_model","entity"]}`, recorriendo `offset` hasta `total`;
   - **de la organización:** el mismo `knowledge_library` con `projectId: "organization"`. Los modelos y sistemas compartidos del cliente pueden vivir ahí: enlázalos por uuid en vez de recrearlos;
   - **por tema:** `knowledge_search` con esos kinds y las palabras del dominio, en español y en inglés.

   Si ya hay un modelo, **extiéndelo**: agrega entidades con `dataModel` apuntando a él. No crees otro.
3. **Fija la fuente.** Un agente debe citar de dónde salió el modelo (`SOURCE_REQUIRED`):
   - `{type:"repo", path:"db/schema.sql", ref:"main"}`;
   - una page de Recursos (`{type:"page", pageId}`);
   - una reunión (`{type:"meeting", title, date}`).
4. **Crea el `data_model`.** `purpose` (15–1500 caracteres) es obligatorio. `engine`, `namespace` (snake_case) y `conventions` son opcionales.
5. **Crea las entidades en orden de dependencia:** primero las referenciadas y después las que las referencian.
   - Una FK que apunta a una entidad que todavía no existe **no falla**: devuelve un warning y la arista no se crea.
   - Si eso ocurre, vuelve a guardar la entidad (`knowledge_get` → `knowledge_update` con las mismas `properties` y `expectedRevision`) cuando el destino exista.
6. **Revisa la respuesta de cada `knowledge_create`:**
   - `warnings`: FK sin resolver, `visibility` degradada;
   - `similar`: posible duplicado. Si es el mismo, para y fusiona.
7. **Verifica con `knowledge_view {view:"erd", scope:"data_model/<slug>", format:"json"}`**: es la misma vista que dibuja el Portal.
   - `tables`: todas tus entidades, con sus columnas.
   - `relations`: **una por columna FK**, también cuando varias apuntan a la misma tabla, con la `cardinality` (`n-1` o `1-1`), `identifying`, `optional` y `onDelete` que esperabas. Cuenta tus columnas con `referencesEntity`: deben ser tantas como relaciones.
   - **`unresolved` vacío.** Si trae FKs, su destino no existe o no es una `entity`. Corrige y vuelve a guardar la entidad.
8. **Entrega** a la persona:
   - **el diagrama dibujado:** `view_render` con un `ErdDiagram` que recibe la respuesta de `knowledge_view` tal cual (skill `views`, «Diagramas de Conocimiento»);
   - las citas `kb:` de cada nodo;
   - si quieren el diagrama en un documento, un bloque `projection` `format: "erd"` en una page v2 (skill `resources` §3), que se dibuja vivo en vez de copiar los datos; uno ya guardado se muestra con `page_projection {path, blockId}`;
   - el Mermaid de la vista (`format:"mermaid"`) si lo pide;
   - el enlace del Portal: el `url` de la vista con el host del Portal delante (`https://app.pai.lat` en producción; en staging, el Portal de staging).

Ejemplo completo y validado (modelo, 5 entidades, FK simple, dos FK a la misma tabla, FK identificante, autorreferencia y enum): `examples/sales-erd.json`.

## Columnas: el contrato exacto

Cada fila de `columns` (de 1 a 80; al menos una `primaryKey`):

| Campo | Regla |
|---|---|
| `name` | `^[a-z][a-z0-9_]*$`, ≤63 caracteres, en inglés y snake_case, único en la entidad |
| `type` | `uuid`, `text`, `integer`, `bigint`, `numeric`, `real`, `boolean`, `date`, `time`, `timestamptz`, `interval`, `jsonb`, `bytea`, `vector` o `enum` |
| `nullable`, `primaryKey`, `unique` | **Obligatorios** (booleanos, sin valor por defecto). Una PK no puede ser `nullable` |
| `referencesEntity` + `referencesColumn` | Van juntos o no van. El primero es `entity/<slug>` |
| `onDelete` | `no_action`, `restrict`, `cascade` o `set_null`. Solo en una FK; `set_null` exige `nullable: true` |
| `enumValues` | Solo con `type: "enum"`, y en ese caso obligatorio (≤50) |
| `isArray`, `default` (≤120), `description` (≤300) | Opcionales |

Otras propiedades de la entidad:
- `physicalName`: la tabla, en snake_case.
- `dataModel`: `["data_model/<slug>"]`, como máximo 1.
- `purpose`: obligatorio, de 15 a 1500 caracteres.
- `invariants`: lista, opcional.
- `lifecycle`: opcional.
- `notes`: opcional.

### Traducción desde SQL

| SQL | Pai |
|---|---|
| `varchar(n)`, `char`, `citext` | `text` (si importa, pon el largo en `description`) |
| `int`, `smallint`, `serial` | `integer`; `bigserial` es `bigint` |
| `decimal(p,s)` | `numeric` |
| `float8`, `double precision` | `real` |
| `timestamp` (sin zona) | `timestamptz`, con la aclaración en `description` |
| `json` | `jsonb` |
| `CREATE TYPE … AS ENUM` | `type:"enum"` + `enumValues` |
| `text[]` | `type:"text"`, `isArray:true` |

## Cardinalidad: cómo se deriva

| Columna FK | Resultado |
|---|---|
| Normal | `n-1` (muchas filas apuntan a una) |
| `unique: true`, o que es toda la PK | `1-1` |
| Parte de la PK | Relación **identificante** |
| `nullable: true` | Relación opcional |
| Muchos a muchos | **Tabla puente** con dos FK en la PK (como `order_line` en el ejemplo) |
| A su propia tabla (`parent_id → id`) | `n-1` sobre sí misma; ponla `nullable: true` (la raíz no tiene padre) |

No existe `n-m` directo.

### Varias FK a la misma tabla y autorreferencias

Son modelado normal y el diagrama las dibuja todas:
- **Varias FK a la misma tabla:** cada columna es su propia relación y su propia línea, con su cardinalidad. Por ejemplo `billing_address_id` y `shipping_address_id` → `address`, o `node_id`, `conflicting_node_id` y `resolution_node_id` → `knowledge_node`. No las juntes en una sola columna ni crees una tabla intermedia para evitarlas.
- **Nombra cada FK por su papel** (`billing_address_id`, no `address_id_2`) y explica la diferencia en `description`: el diagrama distingue las líneas por el nombre de la columna.
- **Autorreferencia** (un árbol: `category.parent_id → category.id`): va `nullable: true`, con `onDelete: "set_null"` o `"cascade"` según si los hijos sobreviven al padre. Se dibuja en el ERD y su `relation` sale en `knowledge_view`, pero no crea una arista `relates_to` (el grafo no admite aristas de un nodo a sí mismo).

## Nombres

- Slugs en inglés y kebab-case: `data_model/sales-model`, `entity/order-line`.
- Columnas y `physicalName` en snake_case.
- Títulos en español («Línea de pedido»).
- Siempre manda `slug` explícito: las referencias (`entity/customer`) dependen de él.
- `idempotencyKey`: `kn-<proyecto>-entity-<slug>`.

## Qué no hacer

- **No** escribas `attributes` ni `relations` (formato v1) ni otras claves: la plantilla es estricta y las rechaza.
- **No** crees aristas `relates_to` a mano ni pongas cardinalidades: salen de las FK.
- **No** escribas Mermaid en `properties` (`MERMAID_NOT_ALLOWED`): el diagrama se genera.
- **No** uses tipos fuera del vocabulario (`varchar`, `string`, `int4`…), ni nombres en camelCase.
- **No** apuntes `referencesEntity` a algo que no sea una `entity`: da warning y no crea la arista.
- **No** pidas `visibility:"client"`: un agente solo escribe `internal`; publicar al cliente lo decide una persona en Console.

## Cambios posteriores

1. `knowledge_get` de la entidad: `revision` y `properties` completas.
2. Modifica la lista `columns` completa.
3. `knowledge_update` con todas las `properties` y `expectedRevision`. Si omites una columna, **se borra**.

Para retirar una entidad usa `knowledge_archive` (con motivo), no la borres. Si cambia la tabla a la que apunta una FK, se recalculan sus aristas.
