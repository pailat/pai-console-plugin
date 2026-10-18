---
description: The resources skill reads an existing whiteboard before appending connected nodes without coordinates, and never replaces it unless asked.
tags: [resources, whiteboard]
runs: 2
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__page_search, mcp__plugin_pai-console_pai__page_list, mcp__plugin_pai-console_pai__whiteboard_read, mcp__plugin_pai-console_pai__whiteboard_update]
---

In Pai, organization df2f92f6-b25e-447d-986d-5d91e690c237, project d69df850-3a6a-4707-baae-a0bc91ae3607: On whiteboard `diagramas/flujo-de-ventas`, append two steps after the existing "Cotización": "Negociación" then "Cierre", connected in that order. The team has already drawn manual content on this whiteboard. Keep its literal path and Spanish labels. Do it without asking questions.
