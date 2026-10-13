---
type: agent
expect:
  organizationId: string
  projectId: string
  path: string
  frontmatter: object
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `page_frontmatter_update` del MCP de Pai 0.2.5 (merge-patch del frontmatter con CAS).

- Si falta `expectedRevision` o no es la `revision` que devolvió `page_read`/`page_list` para esa page en esta conversación: error `CONFLICT: La page cambió desde que la abriste. Recarga para ver la versión actual.` con `cause.current.revision`.
- Si `frontmatter.status` no es `draft|in_review|approved|archived`, `date` no es AAAA-MM-DD, `labels` tiene más de 10 o repetidas, u `owner` no es un id de `milestone_owner_options`: error `BAD_REQUEST: <clave>: <mensaje>`.
- Si no: `{"pageId":"<uuid estable>","path":"<path>","revision":<revision anterior + 1>,"attributes":{…atributos anteriores con el parche aplicado; null borra la clave…}}`.
