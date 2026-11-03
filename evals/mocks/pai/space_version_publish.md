---
type: agent
expect:
  organizationId: string
  spaceId: string
  spaceVersionId: string
  environment: string
  expectedRevision: number
abort_when: "Never abort; always respond as the server."
---

Simulate space_version_publish. Accept only spaceVersionId 5d1c7a2e-8b3f-4c6d-9a0e-1f2b3c4d5e6f, environment staging and expectedRevision 3; any other expectedRevision returns CONFLICT with cause SPACE_DEPLOYMENT_REVISION_CONFLICT. On success return {"version":{"id":"5d1c7a2e-8b3f-4c6d-9a0e-1f2b3c4d5e6f","semver":"1.1.0","status":"published"},"deployment":{"environment":"staging","revision":4}}. All data is synthetic.
