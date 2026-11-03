---
type: agent
expect:
  organizationId: string
  productId: string
  productVersionId: string
  expectedRevision: number
abort_when: "Never abort; always respond as the server."
---

Simulate product_version_publish without contacting Pai. Accept only organizationId 6e5d4c3b-2a19-4807-b6c5-d4e3f2a1b0c9, productId 8a7b6c5d-4e3f-4a2b-9c1d-0e9f8a7b6c5d, productVersionId 4c3b2a19-8f7e-4d6c-9b5a-0e1f2a3b4c5d and expectedRevision 1. Always fail with a BAD_REQUEST error whose reason is PRODUCT_VERSION_BREAKING_REQUIRES_MAJOR: the draft is 1.4.0 with changeKind minor and its pinned API design changed incompatibly since the latest published 1.3.0. Return invalid_input for any other input. All names and identifiers here belong only to synthetic evaluation data.
