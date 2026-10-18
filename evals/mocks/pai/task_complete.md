---
type: agent
expect:
  taskId: string
  expectedRevision: number
abort_when: "Never abort; always respond as the server."
---

Simulate task_complete without contacting Pai. Accept only taskId 11111111-1111-4111-8111-111111111111 with expectedRevision 7 and closeNote "Origin and destination references verified." Otherwise return CONFLICT for an incorrect revision or invalid_input for a different task/note. On success return {"task":{"id":"11111111-1111-4111-8111-111111111111","title":"Review the shipping model","section":"project","status":"done","revision":8},"next":null}. All names and identifiers here belong only to synthetic evaluation data.
