---
description: Issuing a service token searches for the account first, issues exactly one token with the requested narrow scope and expiry, and never repeats the one-time secret in the answer.
tags: [iam]
runs: 2
max_turns: 14
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__organization_list, mcp__plugin_pai-console_pai__iam_service_account_list, mcp__plugin_pai-console_pai__iam_service_account_get, mcp__plugin_pai-console_pai__iam_service_token_list, mcp__plugin_pai-console_pai__iam_service_token_create, mcp__plugin_pai-console_pai__iam_service_token_rotate, mcp__plugin_pai-console_pai__iam_service_account_create]
---

In Pai, issue a service token named "ci-reporter-2026" for the existing service account "ci-reporter" of the Acme QA organization. Scope: the whole organization; permissions: resources.pages.get and resources.pages.list only; expiring on 2026-12-03T00:00:00-06:00. I approve issuing it. This is a simulated development task: do it without asking questions and tell me the result.
