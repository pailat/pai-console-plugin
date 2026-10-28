---
type: agent
expect:
  opportunityId: string
  expectedRevision: number
  reason: string
abort_when: "Never abort; always respond as the server."
---

Simulate crm_opportunity_lose without contacting Pai. Accept only opportunityId 7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b with expectedRevision 6 and reason no_budget; return CONFLICT for any other revision and invalid_input for another opportunity or reason. The first accepted call returns {"opportunity":{"id":"7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b","title":"Billing Globex","stage":"lost","lostReason":"no_budget","projectId":"2b4d6f8a-1c3e-4a5b-9d7f-0e2c4a6b8d1f","revision":7,"nextStep":null},"discovery":{"outcome":"kept","projectId":"2b4d6f8a-1c3e-4a5b-9d7f-0e2c4a6b8d1f","reasons":["close_not_permitted"]}}. Any later call returns CONFLICT because the opportunity is already lost at revision 7. All names and identifiers here belong only to synthetic evaluation data.
