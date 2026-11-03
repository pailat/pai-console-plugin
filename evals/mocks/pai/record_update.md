---
type: agent
expect:
  organizationId: string
  space: string
  recordId: string
  idempotencyKey: string
  expectedRevision: number
  input: object
abort_when: "Never abort; always respond as the server."
---

Simulate record_update for space acme-ledger and record 3e9a1b4c-7d2f-4a60-8b5e-9c1d2e3f4a5b. The first call always fails with PRECONDITION_FAILED, cause {"code":"DATABASE_REVISION_CONFLICT"}, as if another person had changed the record to revision 5, whatever expectedRevision is supplied. Later calls succeed only with expectedRevision 5 and an idempotencyKey different from the first call, returning {"id":"3e9a1b4c-7d2f-4a60-8b5e-9c1d2e3f4a5b","properties":{"title":"Invoice 1042 (reviewed)","status":"open"},"revision":6}. Any other revision returns PRECONDITION_FAILED with cause DATABASE_REVISION_CONFLICT. All data is synthetic.
