---
type: agent
expect:
  opportunityId: string
  expectedRevision: number
  acceptedProposalVersionId: string
  deliveryLeadUserId: string
  startAt: string
  serviceLine: string
  offerings: array
abort_when: "Never abort; always respond as the server."
---

Simulate crm_opportunity_win without contacting Pai. Accept only opportunityId 7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b with expectedRevision 6, acceptedProposalVersionId 5a4b3c2d-1e0f-4a9b-8c7d-6e5f4a3b2c1d, deliveryLeadUserId cb36cf18-405e-4bb7-bb28-849ed71f69d7, startAt 2026-08-01, serviceLine stripe and offerings ["billing"]. Return invalid_input for any other value. If the call has no delivered object, answer {"opportunity":{"id":"7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b","stage":"won","revision":7},"debrief":"created"}. If delivered.closedAt is 2026-09-15, answer {"opportunity":{"id":"7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b","stage":"won","wonAt":"2026-09-15","closedAt":"2026-09-15","revision":7,"history":"ya entregada"},"debrief":"not_created"}; any other delivered date is invalid_input. Any later call returns CONFLICT. All names and identifiers here belong only to synthetic evaluation data.
