---
description: When a Pai Agent turn closes at its per-turn credit budget (K1), the chats skill reports the partial result and pending work and does not send a continuation without the user's go-ahead.
tags: [chats, budget]
runs: 2
max_turns: 14
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__chat_list, mcp__plugin_pai-console_pai__chat_get, mcp__plugin_pai-console_pai__chat_send]
---

In my active Pai Agent chat 3e5a7c9b-1d2f-4a6b-8c0e-2f4a6b8d0e1c, send: "Audit every page of the project and list the ones with outdated sources." Credits are fine for this one message. Then tell me the result. Do not ask me questions before sending.
