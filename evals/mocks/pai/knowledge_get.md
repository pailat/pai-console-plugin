---
type: agent
abort_when: "Never abort; always respond as the server."
---

Act as Pai MCP `knowledge_get`. Return the requested `ref` exactly as created earlier in this conversation, with its original properties and revision: `{"node":{...,"revision":0,"properties":<original properties>},"edges":[...]}`. Derive edges:
- `contains` from the declared `dataModel` or `parent`;
- `relates_to` for each column with `referencesEntity`;
- `uses` or `performs` for each relationship row.

For a node not created earlier, return `NOT_FOUND: No se encontró el nodo.`
