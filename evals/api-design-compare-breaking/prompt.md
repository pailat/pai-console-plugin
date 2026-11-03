---
description: Comparing two saved API revisions uses api_design_review with compareToRevision and reports a breaking change that needs a higher major version, without presenting it as proof.
tags: [api-design]
runs: 2
max_turns: 15
timeout_seconds: 300
allowed_tools: [Read, Skill, mcp__plugin_pai-console_pai__api_design_review, mcp__plugin_pai-console_pai__api_design_get, mcp__plugin_pai-console_pai__api_design_save]
---

In Pai, organization 6e5d4c3b-2a19-4807-b6c5-d4e3f2a1b0c9, API design 9d8c7b6a-5e4f-4a3b-8c2d-1e0f9a8b7c6d: is revision 5 safe to release over revision 3 without bumping the major version? Only review; do not change anything. Do it without asking questions.
