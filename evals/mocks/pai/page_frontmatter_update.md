---
type: agent
expect:
  organizationId: string
  projectId: string
  path: string
  frontmatter: object
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `page_frontmatter_update`, applying a revision-checked merge patch.

- Missing `expectedRevision`, or a mismatch with the revision returned by page_read/page_list for this page: return `CONFLICT: La page cambió desde que la abriste. Recarga para ver la versión actual.` with `cause.current.revision`.
- Reject status outside draft|in_review|approved|archived, dates outside YYYY-MM-DD, duplicate or more than ten labels, or an owner other than the ids listed by milestone_owner_options (exactly `7b1e4c2a-5d3f-4a6b-9c8d-0e1f2a3b4c5d` Laura Méndez, `3c9d8e7f-1a2b-4c3d-8e4f-5a6b7c8d9e0f` Diego Ruiz and `9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d` Sofía Paredes, all valid): `BAD_REQUEST: <key>: <message>`. A name instead of an id is invalid.
- Otherwise return stable pageId, the input path, incremented revision, and previous attributes merged with the patch; null removes a key.
