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
- Reject status outside draft|in_review|approved|archived, dates outside YYYY-MM-DD, duplicate or more than ten labels, or an owner not listed by milestone_owner_options: `BAD_REQUEST: <key>: <message>`.
- Otherwise return stable pageId, the input path, incremented revision, and previous attributes merged with the patch; null removes a key.
