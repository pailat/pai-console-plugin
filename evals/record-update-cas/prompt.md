---
description: record_update carries the revision just read and a fresh idempotencyKey; on DATABASE_REVISION_CONFLICT the agent re-reads instead of overwriting blindly.
tags: [spaces, records]
runs: 2
max_turns: 20
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__space_schema, mcp__plugin_pai-console_pai__record_get, mcp__plugin_pai-console_pai__record_query, mcp__plugin_pai-console_pai__record_update]
---

In Pai, organization 0b6f2d7e-3c4a-4d58-9e1f-2a7b8c9d0e1f, Space `acme-ledger`: set the `title` of record 3e9a1b4c-7d2f-4a60-8b5e-9c1d2e3f4a5b to "Invoice 1042 (reviewed)". Complete the workflow without asking questions.
