---
description: Complete a project task through the unified primitive using a fresh revision, without Knowledge or retired CRM aliases.
tags: [tasks, cas]
runs: 1
max_turns: 18
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__task_list, mcp__plugin_pai-console_pai__task_get, mcp__plugin_pai-console_pai__task_complete]
---

Use the tasks skill. In Pai, finish the project task named "Review the shipping model". Find the existing task, read its current revision and complete it with the closing note "Origin and destination references verified." Do not create another task, change Knowledge, or use CRM task aliases. This is a simulated development task; complete the authorized workflow without asking questions.
