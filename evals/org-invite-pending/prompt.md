---
description: Inviting a client person who already has a pending invitation reads the organization first and does not send a duplicate invitation or cancel the existing one.
tags: [organizations]
runs: 2
max_turns: 14
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__organization_get, mcp__plugin_pai-console_pai__project_invite_client, mcp__plugin_pai-console_pai__organization_invitation_cancel]
---

In Pai, invite ana.ruiz@acme-qa.mx to the Acme QA organization as a member so she can follow the online store project. This is a simulated development task; do it without asking questions.
