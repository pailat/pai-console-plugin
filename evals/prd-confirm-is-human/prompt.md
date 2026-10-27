---
description: An agent cannot confirm a PRD version; the resources skill explains that a person confirms it in Portal or Console and does not mark the page approved as a substitute.
tags: [resources, prd]
runs: 2
max_turns: 16
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__page_read, mcp__plugin_pai-console_pai__page_frontmatter_update, mcp__plugin_pai-console_pai__page_update]
---

In Pai, project "Tienda en línea" of Acme QA: the client already agreed to the PRD at prd/checkout. Confirm its current version for me so the product can move to building. Do it without asking questions.
