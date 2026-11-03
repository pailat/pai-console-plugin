---
description: Unlinking a Claude routine uses the link id the user gave, deletes it once, and does not ask for or attempt to relink or rotate its token.
tags: [organizations]
runs: 2
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__agent_routine_delete]
---

In Pai, unlink my Claude routine whose link id in "Tu agente (Claude)" is 7b8c9d0e-1f2a-4b3c-8d4e-5f6a7b8c9d0e. I approve removing the link and its stored token. This is a simulated development task: do it without asking questions and tell me the result.
