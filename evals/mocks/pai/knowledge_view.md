---
type: agent
expect:
  organizationId: string
  projectId: string
  view: [erd, c4]
  scope: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `knowledge_view`. Return only JSON derived from nodes created earlier in this conversation using `knowledge_create`.

- For `view: erd` scoped to a data_model: return `{"view":"erd","scopeKind":"model","scope":{...},"tables":[{id,name,columns:[...]}],"relations":[{from:{tableId,column},to:{tableId,column},cardinality:"n-1"|"1-1",identifying,optional,onDelete}],"unresolved":[...],"url":"/acme-qa/tienda-en-linea/knowledge/<title-slug>-<shortId>"}`. Unresolved FK targets go in `unresolved`. Emit one relation per FK column, including parallel FKs to one table and self-references with equal source/target table ids.
- For `view: c4` scoped to a component: return `{"view":"c4","level":<requested level or scope level>,"elements":[{id,title,role,c4Type,c4Level,technology}],"relations":[{sourceId,targetId,description,technology}],"tree":[...],"url":"/acme-qa/tienda-en-linea/knowledge/<title-slug>-<shortId>?level=<level>"}`.

For `format: mermaid`, return scope, URL and Mermaid (`erDiagram` or `flowchart`). A missing scope returns `NOT_FOUND: No se encontró el nodo.`
