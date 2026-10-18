---
name: pai-env
description: "Show or change the plugin's Pai MCP environment (staging, develop, or production). Explicit invocation only."
argument-hint: "[staging | develop | production]"
disable-model-invocation: true
allowed-tools: Bash(claude plugin configure:*)
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Pai MCP environment

This source is the **Claude Code** environment adapter. Invoke it explicitly with `/pai-console:pai-env`; never select it automatically. In **Codex**, use the explicitly invoked `pai-env` supplied by the generated environment package and its setup instructions. Do not run Claude configuration commands in Codex or manually edit generated packages. The packaging sources own Codex environment/setup variants.

Codex packages use the unique bundled MCP server names `pai_console_staging`, `pai_console_develop`, and `pai_console_production`, respectively. Use the selected package's matching server for authentication and tool discovery; do not assume a generic `pai` endpoint. The Claude configuration and server name below are unchanged.

Requested environment: `$ARGUMENTS` (empty = show only).

Corp edge URLs:

| Environment | URL |
|---|---|
| staging (default) | `https://mcp-edge-corp-staging.up.railway.app/mcp` |
| develop (without the production guard) | `https://mcp-corp.paitesting.com/mcp` |
| production | `https://mcp-corp.pai.lat/mcp` |

The previous develop URL, `https://mcp-edge-corp-develop.up.railway.app/mcp`, remains accepted during the transition; use the new URL for develop.

1. Show the current value with `claude plugin configure pai-console --json`.
2. If no change was requested, finish with one line naming the current environment.
3. If **production** was requested, confirm with the user first: every production write requires their confirmation.
4. Save the value without printing anything else:
   ```bash
   printf '%s' '{"mcp_url":"<environment URL>"}' | claude plugin configure pai-console --values-stdin
   ```
5. Tell the user to:
   - reload the plugin or restart the session;
   - sign in through `/mcp` (server `plugin:pai-console:pai`), because tokens are URL-specific;
   - check that the session-start environment notice shows the new environment.
