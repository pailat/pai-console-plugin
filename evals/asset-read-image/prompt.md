---
description: The resources skill reads a note's assets list, looks at its screenshot with asset_read (standard size), treats the video through asset_get instead, and does not invent image content the host did not deliver.
tags: [resources, assets, images]
runs: 2
max_turns: 16
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__page_search, mcp__plugin_pai-console_pai__page_list, mcp__plugin_pai-console_pai__page_read, mcp__plugin_pai-console_pai__asset_list, mcp__plugin_pai-console_pai__asset_get, mcp__plugin_pai-console_pai__asset_read]
---

In Pai, project "Tienda en línea" of Acme QA: the note notas/incidente-checkout has a screenshot of the checkout error and a recording. Read the error message shown in the screenshot and tell me how long the recording is. Do it without asking questions.
