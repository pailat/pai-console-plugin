---
description: El skill c4 modela a las personas como actor (nunca c4Type Person), declara technology en contenedores y usa description como etiqueta de las relaciones.
tags: [c4, knowledge]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__knowledge_search, mcp__plugin_pai-console_pai__knowledge_create, mcp__plugin_pai-console_pai__knowledge_get, mcp__plugin_pai-console_pai__knowledge_link]
---

En Pai, organización df2f92f6-b25e-447d-986d-5d91e690c237, proyecto d69df850-3a6a-4707-baae-a0bc91ae3607: documenta la arquitectura C4 (contexto y contenedores) de «Reservas», un sistema donde el cliente final reserva mesas desde una app web en React que llama a una API en Go; la API guarda en PostgreSQL y manda SMS de confirmación con Twilio. La fuente es esta conversación. Hazlo de punta a punta sin preguntarme nada.
