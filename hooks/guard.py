#!/usr/bin/env python3
"""PreToolUse guard for the Pai MCP tools.

Two checks, in this order:

1. Search before create (every environment): a create tool is denied until the
   session has looked for what already exists with a search/list tool of the
   same area. The model reads the reason, searches and tries again.
2. Production (only there): every write asks for confirmation; reads pass. The
   irreversible ones say so and name what they drag along. Nothing is blocked:
   the person decides.

It covers the plugin's server (`mcp__plugin_pai-console_pai__*`, environment from
the plugin's `mcp_url` option) and a user-level `pai-console` server
(`mcp__pai-console__*`, environment from its URL in ~/.claude.json). An unknown
environment counts as production: failing safe means asking once too often.

Reads come from the server's own annotations (hooks/tools.json, generated from
pai-portal 0.2.5+): a tool not in that file counts as a write.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

PLUGIN_PREFIX = "mcp__plugin_pai-console_pai__"
USER_PREFIX = "mcp__pai-console__"

STAGING_HOSTS = (
    "mcp-edge-corp-staging.up.railway.app",
    "mcp-corp.paitesting.com",
    "mcp-edge-corp-develop.up.railway.app",
)

from policy import ATTENTION, IRREVERSIBLE, READ_TOOLS, SEARCH_BEFORE_CREATE


def emit(decision: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )


def environment_of_url(url: str | None) -> str:
    if not url:
        return "production"
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return "production"
    return "staging" if host in STAGING_HOSTS else "production"


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
    """URL of the user-level `pai-console` server, if it is configured there."""
    try:
        config = json.loads((Path.home() / ".claude.json").read_text())
    except (OSError, ValueError):
        return None
    server = (config.get("mcpServers") or {}).get("pai-console") or {}
    return server.get("url")


def tool_environment(tool_name: str) -> tuple[str, str, str] | None:
    """(tool, environment, url) of a Pai tool, or None when it is not one."""
    if tool_name.startswith(PLUGIN_PREFIX):
        url = plugin_url()
        return tool_name[len(PLUGIN_PREFIX) :], environment_of_url(url), url or "?"
    if tool_name.startswith(USER_PREFIX):
        url = user_server_url()
        return tool_name[len(USER_PREFIX) :], environment_of_url(url), url or "?"
    return None


def searched_before(transcript_path: str | None, tools: tuple[str, ...]) -> bool:
    """Whether this session already called one of `tools` on a Pai server."""
    if not transcript_path:
        return True  # nothing to read: never block on a missing transcript
    suffixes = tuple(f"__{tool}" for tool in tools)
    try:
        with open(transcript_path, encoding="utf-8") as transcript:
            for line in transcript:
                if '"tool_use"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(entry, dict) or not isinstance(entry.get("message"), dict):
                    continue
                content = entry["message"].get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "tool_use"
                        and str(item.get("name", "")).startswith(
                            (PLUGIN_PREFIX, USER_PREFIX)
                        )
                        and str(item.get("name", "")).endswith(suffixes)
                    ):
                        return True
    except OSError:
        return True
    return False


def summarize(tool_input: dict) -> str:
    keys = (
        "environment",
        "path",
        "newPath",
        "kind",
        "title",
        "name",
        "status",
        "ref",
        "projectId",
        "productId",
        "milestoneId",
        "proposalId",
        "paymentId",
        "id",
    )
    parts = [
        f"{key}={json.dumps(tool_input[key], ensure_ascii=False)}"
        for key in keys
        if key in tool_input and tool_input[key] not in (None, "")
    ]
    return ", ".join(parts)[:300]


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    if not isinstance(event, dict):
        return
    resolved = tool_environment(str(event.get("tool_name", "")))
    if resolved is None:
        return
    tool, environment, url = resolved
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    if tool in SEARCH_BEFORE_CREATE:
        searches = SEARCH_BEFORE_CREATE[tool]
        if not searched_before(event.get("transcript_path"), searches):
            emit(
                "deny",
                f"Search before creating: this session has not called {' / '.join(searches)}. "
                "Search for existing records (by title, path, or topic), reuse or update them, "
                f"then call {tool} again.",
            )
            return

    if environment != "production" or tool in READ_TOOLS:
        return

    detail = summarize(tool_input)
    where = f"PRODUCTION ({url})"
    if tool in IRREVERSIBLE or tool in ATTENTION:
        irreversible = tool in IRREVERSIBLE and not (
            tool == "product_deploy" and tool_input.get("environment") != "production"
        )
        severity = "IRREVERSIBLE" if irreversible else "ATTENTION"
        consequence = IRREVERSIBLE.get(tool) or ATTENTION[tool]
        emit(
            "ask",
            f"{severity} — {tool} in {where}. {consequence}"
            + (f" Data: {detail}." if detail else "")
            + " Confirm?",
        )
        return
    emit(
        "ask",
        f"Write in {where}: {tool}"
        + (f" ({detail})" if detail else "")
        + ". Confirm?",
    )


if __name__ == "__main__":
    main()
