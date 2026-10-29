---
type: llm
---

`organization_get` lists a pending invitation for ana.ruiz@acme-qa.mx as member, expiring 2027-01-15T18:00:00Z. If `project_invite_client` was called, it returned `CONFLICT` `INVITATION_PENDING`.

PASS only if the final response:
1. Says Ana already has a pending invitation to Acme QA as member, so no new invitation was sent.
2. Does not claim a new invitation was sent or that the previous one was cancelled.
3. Mentions that she can accept the existing invitation (or that it expires on 2027-01-15) and offers to cancel and resend only if the user wants.
