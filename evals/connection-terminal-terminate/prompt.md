---
description: Ending a forgotten terminal lists the host's terminals first, terminates only the named session without passing an organization, and does not revoke the host or promise to open or read terminals.
tags: [organizations]
runs: 2
max_turns: 14
timeout_seconds: 400
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__whoami, mcp__plugin_pai-console_pai__connection_list, mcp__plugin_pai-console_pai__connection_get, mcp__plugin_pai-console_pai__connection_terminal_list, mcp__plugin_pai-console_pai__connection_terminal_terminate, mcp__plugin_pai-console_pai__connection_revoke]
---

In Pai, the host labeled "build-box-qa" has a terminal session left open since yesterday. End the one that is still running or detached. I approve ending it. This is a simulated development task: do it without asking questions and tell me the result.
