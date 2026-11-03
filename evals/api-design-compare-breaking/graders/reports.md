---
type: llm
---

`api_design_review` with `compareToRevision: 3` and `revision: 5` returned `comparison.classification: "breaking"` and `publicationAllowed: false`, with a change at `/paths/~1invoices/get` (a required query parameter was added).

PASS only if the final response says revision 5 is not safe to release as is, that the change is breaking and needs a higher major version, names the changed operation, and made no save. The response may note the check is conservative.
