---
description: Adding an endpoint to an existing API design reads the current document and saves it with CAS instead of importing a duplicate or using generic Knowledge writes.
tags: [api-design, cas]
runs: 2
max_turns: 20
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__api_design_list, mcp__plugin_pai-console_pai__api_design_get, mcp__plugin_pai-console_pai__api_design_save, mcp__plugin_pai-console_pai__api_design_create, mcp__plugin_pai-console_pai__knowledge_update]
---

In Pai, project "Tienda en línea" of Acme QA already has an Orders API design. Add a GET /orders/{orderId} operation that returns 200 with the Order schema and 404 when the order does not exist. Use the api-design skill. This is a simulated development task: make the change without asking questions and tell me the new revision.
