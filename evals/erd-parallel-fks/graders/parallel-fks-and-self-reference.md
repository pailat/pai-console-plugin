---
type: llm
focus: mock_calls
---

PASS solo si en las llamadas a `knowledge_create` se cumple todo esto:
1. La entidad del envío tiene **dos columnas FK distintas** a la entidad de la bodega (`referencesEntity` igual en ambas), nombradas por su papel (por ejemplo `origin_warehouse_id` y `destination_warehouse_id`, nunca `warehouse_id_2`), las dos con `nullable: false`.
2. No hay una tabla intermedia ni una sola columna que junte origen y destino para evitar las dos FK.
3. La entidad de la zona tiene una FK a **sí misma** (`referencesEntity` apunta a su propio slug) con `nullable: true`.
4. La bodega tiene su FK a la zona en una columna (`referencesEntity` + `referencesColumn`).
5. Ninguna llamada usa claves `attributes` o `relations` ni pone Mermaid en `properties`, y todas llevan `sources` no vacío.
