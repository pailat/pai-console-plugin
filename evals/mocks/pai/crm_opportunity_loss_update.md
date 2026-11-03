---
type: agent
expect:
  opportunityId: string
  expectedRevision: number
  reason: string
abort_when: "Never abort; always respond as the server."
---

Simulate crm_opportunity_loss_update without contacting Pai. Accept only opportunityId 7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b with expectedRevision 7 and reason timing; return CONFLICT for another revision and invalid_input for another opportunity or reason. The first accepted call returns {"id":"7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b","title":"Billing Globex","stage":"lost","lostReason":"timing","revision":8,"nextStep":null}. Any later call fails with CRM_LOSS_UNCHANGED. All names and identifiers here belong only to synthetic evaluation data.
