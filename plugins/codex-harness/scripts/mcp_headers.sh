#!/usr/bin/env bash
# headersHelper for the Pai MCP: prints only the Authorization header. The logic is in mcp_headers.py (stdlib only).
exec python3 "$(dirname "${BASH_SOURCE[0]}")/mcp_headers.py" "$@"
