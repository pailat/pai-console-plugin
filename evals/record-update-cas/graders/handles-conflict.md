---
type: llm
---

The mock `record_get` returns revision 4 on the first read and revision 5 after a first `record_update` attempt failed with `DATABASE_REVISION_CONFLICT`. PASS only if: the first `record_update` used `expectedRevision` 4 and an `idempotencyKey`; after the conflict the agent re-read the record with `record_get`; the retry used `expectedRevision` 5 and a different `idempotencyKey` (or it stopped and explained the conflict to the person); it never reused the stale revision. FAIL if it retried with revision 4, omitted either control, or claimed success without a successful `record_update`.
