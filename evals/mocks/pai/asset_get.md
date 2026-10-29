---
type: agent
expect:
  organizationId: string
  assetId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `asset_get`. For assetId `8a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d` return `{"id":"8a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d","filename":"grabacion-checkout.mp4","kind":"video","contentType":"video/mp4","sizeBytes":4812000,"width":1280,"height":720,"durationMs":42000,"status":"ready","uploadedBy":{"name":"Persona QA"},"href":"/api/pages/assets/8a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d","usedIn":[{"documentId":"9c1d2e3f-4a5b-4c6d-8e7f-90a1b2c3d4e5","title":"Incidente en checkout","path":"notas/incidente-checkout","format":"markdown"}],"canDelete":false}`. For `3f1c2a9e-7b4d-4c8e-9a1f-2b3c4d5e6f70` return the same shape for `error-checkout.png` (image/png, 27412 bytes, 1330×194, no durationMs). Any other id: `NOT_FOUND: Asset no encontrado.`
