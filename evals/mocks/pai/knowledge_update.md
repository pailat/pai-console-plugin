---
type: agent
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `knowledge_update`. For any node of kind api, return `FORBIDDEN: Un diseño de API se edita en «Diseño de API» o con api_design_save, no con las herramientas genéricas de Knowledge.` with cause `{"code":"API_DESIGN_OWNED","tool":"api_design_save"}`. For other nodes return `NOT_FOUND: No se encontró el nodo.` Synthetic evaluation data.
