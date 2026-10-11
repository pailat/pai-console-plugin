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

STAGING_HOSTS = ("mcp-edge-corp-staging.up.railway.app", "mcp-edge-corp-develop.up.railway.app")


def environment_of_url(url: str | None) -> str:
    if not url:
        return "production"
    return "staging" if any(host in url for host in STAGING_HOSTS) else "production"


def label(environment: str) -> str:
    return "STAGING" if environment == "staging" else "PRODUCCIÓN"


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
        f"MCP de Pai (plugin pai-console): entorno {label(environment)}, servidor `pai` en {url or 'sin configurar'}.",
        "Sus tools se llaman mcp__plugin_pai-console_pai__<tool>. Si responden 401 o no aparecen, la persona inicia sesión en /mcp (servidor plugin:pai-console:pai, OAuth de Console).",
        "Cambiar de entorno: /pai-console:pai-env (luego volver a iniciar sesión en /mcp).",
    ]
    if environment == "production":
        lines.append(
            "En producción cada escritura pide confirmación a la persona; no la des por hecha y no reintentes una escritura rechazada."
        )
    user_url = user_server_url()
    if user_url:
        lines.append(
            f"También existe el servidor de usuario `pai-console` (tools mcp__pai-console__*) en {user_url}: {label(environment_of_url(user_url))}. "
            "Para trabajar usa las tools del plugin salvo que la persona pida ese servidor."
        )
    print(
        json.dumps(
            {
                "systemMessage": f"Pai MCP: {label(environment)} ({url or 'sin configurar'})",
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
