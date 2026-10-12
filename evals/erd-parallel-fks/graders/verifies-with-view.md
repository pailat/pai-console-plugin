---
type: tool_order
before: { tool: mcp__plugin_pai-console_pai__knowledge_create, input_match: '"kind"\s*:\s*"entity"' }
after: { tool: mcp__plugin_pai-console_pai__knowledge_view, input_match: '"view"\s*:\s*"erd"' }
---
