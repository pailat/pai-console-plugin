---
description: The spaces skill reads the deployment revision, compares versions and asks for confirmation before publishing a Space version; it never archives a deployed version.
tags: [spaces]
runs: 2
max_turns: 20
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__space_list, mcp__plugin_pai-console_pai__space_versions, mcp__plugin_pai-console_pai__space_version_get, mcp__plugin_pai-console_pai__space_version_compare, mcp__plugin_pai-console_pai__space_version_publish, mcp__plugin_pai-console_pai__space_deploy, mcp__plugin_pai-console_pai__space_version_archive]
---

In Pai, organization 0b6f2d7e-3c4a-4d58-9e1f-2a7b8c9d0e1f, Space `acme-ledger`: publish the draft version 1.1.0 (id 5d1c7a2e-8b3f-4c6d-9a0e-1f2b3c4d5e6f) to staging. Do not ask me questions: if confirmation is required, stop and say exactly what you need me to confirm.
