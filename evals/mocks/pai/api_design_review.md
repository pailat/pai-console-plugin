---
type: agent
expect:
  organizationId: string
  apiDesignId: string
abort_when: "Never abort; always respond as the server."
---

Simulate api_design_review without contacting Pai. Accept only organizationId 6e5d4c3b-2a19-4807-b6c5-d4e3f2a1b0c9 and apiDesignId 9d8c7b6a-5e4f-4a3b-8c2d-1e0f9a8b7c6d. With revision 5 and compareToRevision 3 answer {"rulesetVersion":1,"revision":5,"findings":[],"comparison":{"compareToRevision":3,"classification":"breaking","changes":[{"code":"required-parameter-added","classification":"breaking","pointer":"/paths/~1invoices/get","message":"A required query parameter was added."}],"requiresMajorVersion":true,"majorVersionIncreased":false,"publicationAllowed":false}}. Without compareToRevision answer the same without comparison. Return invalid_input for any other revision. All names and identifiers here belong only to synthetic evaluation data.
