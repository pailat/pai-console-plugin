---
description: El skill theme arma un tema completo desde la marca (conserva el logo publicado), lo previsualiza, corrige el contraste AA que reporta el servidor y lo deja como borrador sin publicarlo.
tags: [theme]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, Agent, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__organization_theme_get, mcp__plugin_pai-console_pai__organization_theme_preview, mcp__plugin_pai-console_pai__organization_theme_save_draft, mcp__plugin_pai-console_pai__organization_theme_publish]
---

En Pai, organización df2f92f6-b25e-447d-986d-5d91e690c237 (Acme QA): quiero que su Portal use la marca de Acme. Verde #0f766e como color principal (en oscuro #2dd4bf), acento #f0fdfa en claro y #134e4a en oscuro, fuente Plus Jakarta Sans, esquinas un poco más redondeadas que las de Pai y la barra lateral flotante. Déjalo como borrador para que lo revise; todavía no lo publiques. Hazlo sin preguntarme nada.
