---
description: El skill resources guarda un prototipo interactivo como bloque html (sin typeSlug, sin red, scripts de un CDN permitido y tokens de Pai), validado antes de crear.
tags: [resources, html]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__page_search, mcp__plugin_pai-console_pai__page_list, mcp__plugin_pai-console_pai__page_validate, mcp__plugin_pai-console_pai__page_create]
---

En Pai, organización df2f92f6-b25e-447d-986d-5d91e690c237, proyecto d69df850-3a6a-4707-baae-a0bc91ae3607: guarda en Recursos, para el equipo, un prototipo interactivo de simulador de cuotas: un slider de monto (de $10,000 a $500,000 MXN), un selector de plazo (6, 12 o 24 meses) con tasa anual fija de 18 % y una gráfica de barras con el pago mensual de cada plazo usando Chart.js. Que se vea bien en modo claro y oscuro. Hazlo de punta a punta sin preguntarme nada.
