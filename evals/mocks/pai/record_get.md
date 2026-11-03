---
type: agent
abort_when: "Never abort; always respond as the server."
---

Simulate record_get for space acme-ledger and recordId 3e9a1b4c-7d2f-4a60-8b5e-9c1d2e3f4a5b. Return {"id":"3e9a1b4c-7d2f-4a60-8b5e-9c1d2e3f4a5b","properties":{"title":"Invoice 1042","status":"open"},"revision":4} on the first call. After a record_update has failed with DATABASE_REVISION_CONFLICT, return the same record with revision 5 and title "Invoice 1042 (edited elsewhere)". After a successful record_update, return the updated record. All data is synthetic.
