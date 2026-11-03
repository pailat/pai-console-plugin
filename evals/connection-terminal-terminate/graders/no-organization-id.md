---
type: llm
---

The `connection_*` tools take no `organizationId`.

PASS only if no `connection_*` call in the trace carried an `organizationId` input, and the final response says the open session is now closing or closed (as the tool returned), names the host, and does not claim it can open, read or write a terminal or that the host was revoked.
