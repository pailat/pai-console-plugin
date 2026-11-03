---
description: A mistaken loss reason on an already lost deal is fixed with crm_opportunity_loss_update (CAS, no second loss), and the skill reports that stage and Discovery were not touched.
tags: [crm]
runs: 2
max_turns: 15
timeout_seconds: 300
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__crm_opportunity_loss_update, mcp__plugin_pai-console_pai__crm_opportunity_lose, mcp__plugin_pai-console_pai__crm_opportunity_archive]
---

In Pai CRM, opportunity 7c2e4f1a-9b3d-4e5f-8a6b-1c2d3e4f5a6b (Billing Globex) is already lost at revision 7 with reason no_budget. The real reason was timing: the client postponed to next year. Correct it. Do it without asking questions.
