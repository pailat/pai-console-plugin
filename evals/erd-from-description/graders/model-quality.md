---
type: llm
focus: mock_calls
---

PASS solo si en las llamadas a `knowledge_create` se cumple todo esto:
1. Hay un `data_model` y al menos dos `entity` (autor y libro) con `slug` en inglés y kebab-case.
2. Cada entidad tiene `properties.dataModel` apuntando al data_model y `columns` en las que **cada** columna declara `name` en snake_case, un `type` del vocabulario cerrado (uuid, text, integer, bigint, numeric, real, boolean, date, time, timestamptz, interval, jsonb, bytea, vector, enum) y los tres booleanos `nullable`, `primaryKey` y `unique`. Ningún `varchar`.
3. La columna del ISBN es `unique: true`. La FK del libro al autor está en la columna (`referencesEntity` + `referencesColumn`), con `nullable: false`.
4. Ninguna llamada usa claves `attributes` o `relations`, ni pone Mermaid en `properties`.
5. Todas llevan `sources` no vacío.
