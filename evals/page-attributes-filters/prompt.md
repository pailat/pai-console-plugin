---
description: The resources skill filters pages on the server and updates attributes with a revision-checked merge patch without rewriting content.
tags: [resources, attributes]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__project_list, mcp__plugin_pai-console_pai__page_search, mcp__plugin_pai-console_pai__page_list, mcp__plugin_pai-console_pai__page_read, mcp__plugin_pai-console_pai__page_validate, mcp__plugin_pai-console_pai__milestone_owner_options, mcp__plugin_pai-console_pai__page_frontmatter_update, mcp__plugin_pai-console_pai__page_update]
---

In Pai, organization df2f92f6-b25e-447d-986d-5d91e690c237, project d69df850-3a6a-4707-baae-a0bc91ae3607: List payment pages with the literal label "pagos" that are still in review. Approve the payment reconciliation page, set date 2026-10-12 and owner Laura Méndez, and leave its content untouched. Keep the existing Spanish page titles in the response. Do it without asking questions.
