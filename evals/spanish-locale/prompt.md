---
description: English-authored skills still answer a Spanish-speaking user in Spanish and preserve Mexico City business formatting.
tags: [locale, views]
runs: 2
max_turns: 20
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__payment_list]
---

<!-- Intentional literal Spanish user input for multilingual regression. -->
En Pai, organización df2f92f6-b25e-447d-986d-5d91e690c237, proyecto d69df850-3a6a-4707-baae-a0bc91ae3607: dame un resumen breve de los cobros en español, con importes en MXN y la fecha del siguiente cobro. No guardes una página ni cambies nada.
