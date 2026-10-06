---
description: El skill erd busca antes de crear, crea data_model y entidades con columnas tipadas y no escribe aristas a mano.
tags: [erd, knowledge]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__knowledge_search, mcp__plugin_pai-console_pai__knowledge_library, mcp__plugin_pai-console_pai__knowledge_view, mcp__plugin_pai-console_pai__knowledge_create, mcp__plugin_pai-console_pai__knowledge_get, mcp__plugin_pai-console_pai__knowledge_link]
---

En Pai, organización df2f92f6-b25e-447d-986d-5d91e690c237, proyecto d69df850-3a6a-4707-baae-a0bc91ae3607: modela el ERD de una biblioteca en PostgreSQL. Hay autores (nombre) y libros (título, ISBN único, autor obligatorio). La fuente es esta conversación. Hazlo de punta a punta sin preguntarme nada.
