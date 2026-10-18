---
description: The erd skill searches before creating a data_model and typed entities, without writing manual relationship edges.
tags: [erd, knowledge]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__knowledge_search, mcp__plugin_pai-console_pai__knowledge_library, mcp__plugin_pai-console_pai__knowledge_view, mcp__plugin_pai-console_pai__knowledge_create, mcp__plugin_pai-console_pai__knowledge_get, mcp__plugin_pai-console_pai__knowledge_link]
---

In Pai, organization df2f92f6-b25e-447d-986d-5d91e690c237, project d69df850-3a6a-4707-baae-a0bc91ae3607: Model a PostgreSQL library ERD with authors (name) and books (title, unique ISBN, required author). Use this conversation as the source. Complete the workflow without asking questions.
