---
description: Un resumen visual pedido en la conversación se dibuja con view_render, sin guardar una page, solo con los datos que devolvió payment_list.
tags: [views]
runs: 2
max_turns: 20
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__payment_list, mcp__plugin_pai-console_pai__view_catalog, mcp__plugin_pai-console_pai__view_render, mcp__plugin_pai-console_pai__page_create]
---

En Pai, organización df2f92f6-b25e-447d-986d-5d91e690c237, proyecto d69df850-3a6a-4707-baae-a0bc91ae3607: muéstrame visualmente cómo vamos con los cobros del proyecto.
