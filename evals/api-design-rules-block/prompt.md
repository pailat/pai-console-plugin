---
description: A save refused by the API design rules (API_DESIGN_RULES) is fixed at the reported pointer and saved again, without deleting the operation or error response.
tags: [api-design, rules]
runs: 2
max_turns: 22
timeout_seconds: 450
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__api_design_list, mcp__plugin_pai-console_pai__api_design_get, mcp__plugin_pai-console_pai__api_design_save, mcp__plugin_pai-console_pai__api_design_review]
---

In Pai, project "Tienda en línea" of Acme QA has an Orders API design. Add GET /orders/{orderId}: 200 returns the Order schema, and 404 returns application/json content when the order does not exist (write that 404 response with content but without a schema first, exactly as I describe it). If Pai rejects the save, fix what it reports and save again. This is a simulated development task: do it without asking questions and tell me the final revision.
