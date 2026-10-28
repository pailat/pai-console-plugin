---
type: agent
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `project_invite_client` without contacting Pai. For email ana.ruiz@acme-qa.mx in organization df2f92f6-b25e-447d-986d-5d91e690c237, return `CONFLICT: Ya hay una invitación pendiente para este correo.` with cause `{"code":"INVITATION_PENDING"}`. For any other email return `{"id":"2e4a6c8e-0b2d-4f6a-8c0e-2b4d6f8a0c2e","email":"<input email>","role":"<input role or owner>","status":"pending","expiresAt":"2026-10-29T18:00:00.000Z"}`. Synthetic evaluation data.
