---
description: Losing a deal returns { opportunity, discovery }; when Discovery is kept for close_not_permitted, the crm skill reports it and neither retries the loss nor closes the project another way.
tags: [crm]
runs: 2
max_turns: 20
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__crm_opportunity_get, mcp__plugin_pai-console_pai__crm_opportunity_lose, mcp__plugin_pai-console_pai__project_close, mcp__plugin_pai-console_pai__project_reopen]
---

In Pai CRM, mark opportunity 7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b (Billing Globex) as lost: the client has no budget this year. Then tell me what happened to its Discovery project. Do it without asking questions.
