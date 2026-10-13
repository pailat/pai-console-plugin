---
description: El skill resources filtra pages por estatus y etiqueta con page_list y cambia atributos con page_frontmatter_update (merge-patch, responsable de milestone_owner_options, expectedRevision), sin reescribir la page.
tags: [resources, attributes]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__page_search, mcp__plugin_pai-console_pai__page_list, mcp__plugin_pai-console_pai__page_read, mcp__plugin_pai-console_pai__page_validate, mcp__plugin_pai-console_pai__milestone_owner_options, mcp__plugin_pai-console_pai__page_frontmatter_update, mcp__plugin_pai-console_pai__page_update]
---

En Pai, organización df2f92f6-b25e-447d-986d-5d91e690c237, proyecto d69df850-3a6a-4707-baae-a0bc91ae3607: dime qué pages de pagos (etiqueta «pagos») siguen en revisión. La de conciliación de pagos márcala como aprobada, con fecha 2026-10-12 y con Laura Méndez como responsable; no toques su contenido. Hazlo sin preguntarme nada.
