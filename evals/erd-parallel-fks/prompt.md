---
description: The erd skill models parallel foreign keys as role-named columns and a nullable self-reference, then verifies with knowledge_view.
tags: [erd, knowledge]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__knowledge_search, mcp__plugin_pai-console_pai__knowledge_library, mcp__plugin_pai-console_pai__knowledge_view, mcp__plugin_pai-console_pai__knowledge_create, mcp__plugin_pai-console_pai__knowledge_get, mcp__plugin_pai-console_pai__knowledge_link]
---

In Pai, organization df2f92f6-b25e-447d-986d-5d91e690c237, project d69df850-3a6a-4707-baae-a0bc91ae3607: Model a PostgreSQL shipping ERD. A shipment leaves an origin warehouse and arrives at a destination warehouse; both are required. Warehouses belong to zones, and a zone may be inside another zone (the root zone has no parent). Use this conversation as the source. Complete the workflow without asking questions.
