#!/usr/bin/env python3
"""SessionStart: say which Pai environment the MCP is on, to the person and to the model.

The model gets it as context so it never assumes staging while writing to production;
the person sees one line. When a user-level `pai-console` server also exists, the model
is told which environment each one points at, so it picks the plugin's tools.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

STAGING_HOSTS = ("mcp-edge-corp-staging.up.railway.app",)
DEVELOP_HOSTS = ("mcp-corp.paitesting.com", "mcp-edge-corp-develop.up.railway.app")
LABELS = {"staging": "STAGING", "develop": "DEVELOP", "production": "PRODUCTION"}


def environment_of_url(url: str | None) -> str:
    if not url:
        return "production"
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return "production"
    if host in DEVELOP_HOSTS:
        return "develop"
    return "staging" if host in STAGING_HOSTS else "production"


def label(environment: str) -> str:
    return LABELS[environment]


def plugin_url() -> str | None:
    """The plugin server's URL: the configured option, else the manifest default.

    Claude Code exports CLAUDE_PLUGIN_OPTION_MCP_URL only once the option has
    been set; until then the server runs on the manifest default, so the hooks
    read that same default instead of guessing.
    """
    url = os.environ.get("CLAUDE_PLUGIN_OPTION_MCP_URL")
    if url:
        return url
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).resolve().parent.parent)
    try:
        manifest = json.loads((Path(root) / ".claude-plugin" / "plugin.json").read_text())
    except (OSError, ValueError):
        return None
    return ((manifest.get("userConfig") or {}).get("mcp_url") or {}).get("default")


def user_server_url() -> str | None:
    try:
        config = json.loads((Path.home() / ".claude.json").read_text())
    except (OSError, ValueError):
        return None
    server = (config.get("mcpServers") or {}).get("pai-console") or {}
    return server.get("url")


def main() -> None:
    url = plugin_url()
    environment = environment_of_url(url)
    lines = [
        f"Pai MCP (pai-console plugin): environment {label(environment)}, server `pai` at {url or 'not configured'}.",
        "Its tools are named mcp__plugin_pai-console_pai__<tool>. If they return 401 or are missing, sign in through /mcp (server plugin:pai-console:pai, Console OAuth).",
        "Switch environments: /pai-console:pai-env (then sign in again through /mcp).",
    ]
    if environment == "production":
        lines.append(
            "In production every write requests confirmation from the user; do not assume approval or retry a rejected write."
        )
    user_url = user_server_url()
    if user_url:
        lines.append(
            f"There is also a user server `pai-console` (tools mcp__pai-console__*) at {user_url}: {label(environment_of_url(user_url))}. "
            "Use the plugin tools unless the user requests that server."
        )
    print(
        json.dumps(
            {
                "systemMessage": f"Pai MCP: {label(environment)} ({url or 'not configured'})",
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": "\n".join(lines),
                },
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
