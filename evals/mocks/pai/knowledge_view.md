---
type: agent
expect:
  organizationId: string
  projectId: string
  view: [erd, c4]
  scope: string
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `knowledge_view` del MCP de Pai 0.2.5. Responde solo con JSON derivado **de los nodos creados antes en esta conversación** con `knowledge_create`.

- **`view: "erd"`** (scope: un `data_model`): `{"view":"erd","scopeKind":"model","scope":{...},"tables":[{id,name,columns:[...]}],"relations":[{from:{tableId,column},to:{tableId,column},cardinality:"n-1"|"1-1",identifying,optional,onDelete}],"unresolved":[...],"url":"/portal/organization/projects/<projectId>/knowledge/<id>"}`. Una FK cuyo `referencesEntity` no corresponde a una entidad creada va en `unresolved`.
- **`view: "c4"`** (scope: un `component`, `level` o el nivel del scope): `{"view":"c4","level":<level>,"elements":[{id,title,role,c4Type,c4Level,technology}],"relations":[{sourceId,targetId,description,technology}],"tree":[...],"url":"/portal/organization/projects/<projectId>/knowledge/<id>?level=<level>"}`.

Con `format: "mermaid"` devuelve `{"scope":...,"url":...,"mermaid":"erDiagram …"}` o `flowchart`. Si el scope no existe: error `NOT_FOUND: No se encontró el nodo.`
