---
type: llm
focus: mock_calls
---

PASS solo si en las llamadas a `knowledge_create` se cumple todo esto:
1. Hay un `actor` para el cliente final y ningún `component` con `c4Type: "Person"`.
2. Hay un `component` de nivel `context` (`c4Type: System`) para Reservas y uno `System_Ext` para Twilio.
3. Los contenedores (web, API, base de datos) son `c4Level: "container"`, llevan `technology` (React, Go, PostgreSQL), y `parent` apunta al sistema (`component/<slug>`).
4. Las relaciones van en `properties.relationships` con `to`, `direction`, `description` (un verbo y su objeto) y `technology` cuando aplica. No hay ningún campo `label`. La relación con el actor usa `direction: "in"`.
5. Slugs en inglés y kebab-case; todas las llamadas llevan `sources` no vacío.
