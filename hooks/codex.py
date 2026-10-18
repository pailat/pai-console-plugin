#!/usr/bin/env python3
"""Codex lifecycle adapter for the fixed, packaged Pai endpoint.

Packaging must select ./hooks/codex_hooks.json explicitly, place environment.json
at PLUGIN_ROOT, and configure native MCP write approvals. This adapter never
allows a permission request or asks for approval. See hooks/README.md.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

from policy import ATTENTION, IRREVERSIBLE, READ_TOOLS, SEARCH_BEFORE_CREATE

ENVIRONMENTS = {
    "development": "develop", "develop": "develop",
    "staging": "staging", "production": "production",
}
HOSTS = {
    "mcp-corp.paitesting.com": "develop",
    "mcp-edge-corp-develop.up.railway.app": "develop",
    "mcp-edge-corp-staging.up.railway.app": "staging",
    "mcp-corp.pai.lat": "production",
}
SEARCHES = frozenset(name for names in SEARCH_BEFORE_CREATE.values() for name in names)


class PolicyError(Exception):
    """Missing or invalid policy evidence must not authorize a write."""


def package() -> dict:
    root = Path(os.environ.get("PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
    try:
        config = json.loads((root / "environment.json").read_text())
        if not isinstance(config, dict):
            raise ValueError
        environment = ENVIRONMENTS.get(config.get("environment"))
        url = config.get("url")
        plugin = config.get("plugin_name")
        if not isinstance(url, str) or not isinstance(plugin, str):
            raise ValueError
        parsed = urlsplit(url)
        if (environment is None or config.get("server_name") != f"pai_console_{environment}"
                or plugin != f"pai-console-{environment}"
                or parsed.scheme != "https" or parsed.username or parsed.password
                or parsed.port not in (None, 443) or parsed.query or parsed.fragment
                or parsed.path != "/mcp" or HOSTS.get(parsed.hostname) != environment):
            raise ValueError
        return {"environment": environment, "url": url,
                "plugin_name": plugin, "server_name": f"pai_console_{environment}"}
    except (OSError, ValueError, TypeError):
        raise PolicyError("Missing or invalid packaged environment.json; Pai calls are blocked.") from None


def resolve(name: str, config: dict) -> tuple[str, str] | None:
    """Resolve only complete known server names, never suffix or substring matches.

    The canonical server namespace is unique to the packaged environment.
    Generic Pai aliases never provide evidence for this package. Code mode delivers nested calls via
    the same hook path, so no JavaScript or transcript parsing is necessary.
    """
    prefixes = known_prefixes(config)
    for prefix in prefixes:
        if name.startswith(prefix):
            tool = name[len(prefix):]
            if re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", tool):
                return prefix, tool
    return None


def pai_like(name: str) -> bool:
    """Unknown Pai namespaces are denied rather than assigned a guessed endpoint."""
    return bool(re.match(r"^mcp__(?:pai|plugin(?:_{1,2}|-)pai)", name, re.IGNORECASE))


def output(event: str, reason: str, *, deny: bool = False) -> dict:
    if deny and event == "PostToolUse":
        return {"decision": "block", "reason": reason}
    specific = {"hookEventName": event}
    if deny and event == "PreToolUse":
        specific.update(permissionDecision="deny", permissionDecisionReason=reason)
    else:
        specific["additionalContext"] = reason
    return {"hookSpecificOutput": specific}


def initial_state() -> dict:
    return {"version": 1, "searches": [], "identity": None, "ended": False}


def validate_state(state: object) -> dict:
    if (not isinstance(state, dict) or state.get("version") != 1
            or not isinstance(state.get("searches"), list)
            or any(not isinstance(x, str) or x not in SEARCHES for x in state["searches"])
            or state.get("identity") not in (None, "develop", "staging", "production", "unknown")
            or type(state.get("ended")) is not bool):
        raise PolicyError("Corrupt Pai session state; start a new session and repeat identity and searches.")
    return state


@contextmanager
def state_for(session: object, server: str, config: dict):
    """Serialize read/modify/write on a stable lock inode; atomically replace data."""
    if not isinstance(session, str) or not session.strip():
        raise PolicyError("Missing session_id; Pai writes require isolated session evidence.")
    data = os.environ.get("PLUGIN_DATA")
    if not data or not Path(data).is_absolute():
        raise PolicyError("Missing absolute PLUGIN_DATA; Pai writes require persistent session evidence.")
    directory = Path(data) / "pai-hook-state"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    key = hashlib.sha256(json.dumps([session, server, config], sort_keys=True).encode()).hexdigest()
    path = directory / f"{key}.json"
    with (directory / f"{key}.lock").open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            try:
                state = validate_state(json.loads(path.read_text()))
            except FileNotFoundError:
                state = initial_state()
            except (ValueError, UnicodeError):
                raise PolicyError("Corrupt Pai session state; start a new session and repeat identity and searches.") from None
            yield state
            fd, temporary = tempfile.mkstemp(prefix=f".{key}.", dir=directory)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump(state, stream, sort_keys=True)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def successful_payload(response: object) -> dict | None:
    """Accept MCP JSON carriers or explicit Pai success, never arbitrary text.

    Inspect every carrier and data wrapper so an outer transport success cannot
    hide an inner application failure. Empty JSON searches are valid; missing
    responses and malformed/error results are not evidence.
    """
    def decode(value: object, trusted: bool = False, depth: int = 0):
        if depth > 20:
            return None
        if isinstance(value, list):
            return {"data": value} if trusted else None
        if not isinstance(value, dict):
            return None
        if "isError" in value and value["isError"] is not False:
            return None
        if "success" in value and value["success"] is not True:
            return None
        if value.get("error") is not None or value.get("errors"):
            return None
        if value.get("status") in ("error", "failed", "failure"):
            return None
        payloads = []
        if "structuredContent" in value:
            payload = decode(value["structuredContent"], True, depth + 1)
            if payload is None:
                return None
            payloads.append(payload)
        if "content" in value:
            content = value["content"]
            if not isinstance(content, list) or not content:
                return None
            for block in content:
                if (not isinstance(block, dict) or block.get("type") != "text"
                        or not isinstance(block.get("text"), str)):
                    return None
                try:
                    decoded = json.loads(block["text"])
                except ValueError:
                    return None
                payload = decode(decoded, True, depth + 1)
                if payload is None:
                    return None
                payloads.append(payload)
        if payloads:
            return payloads[0]
        trusted = trusted or value.get("success") is True
        if "data" in value:
            return decode(value["data"], trusted or value.get("isError") is False, depth + 1)
        return value if trusted else None

    return decode(response)


def handle(event: dict) -> dict | None:
    kind = event.get("hook_event_name")
    if kind not in ("SessionStart", "PreToolUse", "PostToolUse", "SessionEnd"):
        return output("PreToolUse", "Malformed or unsupported Pai hook event.", deny=True)
    name = event.get("tool_name", "")
    if not isinstance(name, str):
        return output(kind, "Malformed tool_name.", deny=True)
    # Native local tools, including code-mode exec, are outside Pai policy. Nested
    # MCP invocations get their own PreToolUse/PostToolUse events from Codex.
    if kind in ("PreToolUse", "PostToolUse") and not name.startswith("mcp__"):
        return None
    if kind in ("PreToolUse", "PostToolUse") and not pai_like(name):
        return None
    try:
        config = package()
        if kind == "SessionStart":
            text = (f"Pai MCP: {config['environment'].upper()} ({config['url']}); "
                    f"plugin {config['plugin_name']}, server {config['server_name']}. This package uses a fixed endpoint. "
                    "Call whoami before non-CRM writes. CRM-only access uses this packaged endpoint. "
                    "Search before creating. Native MCP approval policies must confirm production writes; "
                    "hooks do not grant approval or replace server authorization, CAS, or idempotency.")
            return {"systemMessage": f"Pai MCP: {config['environment'].upper()} ({config['url']})",
                    **output(kind, text)}
        if kind == "SessionEnd":
            # Mark every exact namespace for this package, preserving lock files.
            for prefix in known_prefixes(config):
                with state_for(event.get("session_id"), prefix, config) as state:
                    state.update(initial_state(), ended=True)
            return None
        resolved = resolve(name, config)
        if resolved is None:
            return output(kind, "Unknown Pai server namespace; use the packaged Pai server.", deny=True) if pai_like(name) else None
        server, tool = resolved
        if not isinstance(event.get("tool_input"), dict):
            return output(kind, "Malformed Pai tool_input; expected an object.", deny=True)
        if kind == "PostToolUse":
            if tool not in SEARCHES and tool != "whoami":
                return None
            payload = successful_payload(event.get("tool_response"))
            with state_for(event.get("session_id"), server, config) as state:
                if state["ended"]:
                    raise PolicyError("Pai session has ended; start a new session.")
                if tool == "whoami":
                    identity = ENVIRONMENTS.get(payload.get("environment")) if payload and isinstance(payload.get("environment"), str) else None
                    state["identity"] = identity or "unknown"
                    if state["identity"] != config["environment"]:
                        # Persist the mismatch before reporting feedback.
                        result = output(kind, "whoami environment does not match the packaged endpoint; Pai writes are blocked.", deny=True)
                    else:
                        result = None
                else:
                    # A failed refresh must not leave stale evidence for that tool.
                    state["searches"] = sorted((set(state["searches"]) - {tool}) | ({tool} if payload is not None else set()))
                    result = None
            return result
        if tool in READ_TOOLS:
            return None
        if tool not in inventory_tools():
            return output(kind, f"Unknown Pai tool {tool}; update the literal inventory and native approvals before writing.", deny=True)
        with state_for(event.get("session_id"), server, config) as state:
            if state["ended"]:
                raise PolicyError("Pai session has ended; start a new session.")
            if state["identity"] not in (None, config["environment"]):
                raise PolicyError("whoami environment does not match the packaged endpoint; repeat whoami before writing.")
            if not tool.startswith("crm_") and state["identity"] is None:
                raise PolicyError("Call whoami on this server before writing and verify its environment.")
            if tool in SEARCH_BEFORE_CREATE and not set(SEARCH_BEFORE_CREATE[tool]).intersection(state["searches"]):
                raise PolicyError(f"Search before creating: call {' / '.join(SEARCH_BEFORE_CREATE[tool])} successfully on this server in this session before {tool}.")
        consequence = IRREVERSIBLE.get(tool) or ATTENTION.get(tool)
        text = f"Pai write: {tool} in {config['environment'].upper()} ({config['url']})."
        if consequence:
            severity = "IRREVERSIBLE" if tool in IRREVERSIBLE and not (tool == "product_deploy" and event["tool_input"].get("environment") != "production") else "ATTENTION"
            text += f" {severity}: {consequence}"
        if config["environment"] == "production":
            text += " Native MCP approval is required by package policy; this hook does not grant approval."
        return output(kind, text)
    except (PolicyError, OSError) as error:
        return output(kind, str(error) if isinstance(error, PolicyError) else "Pai session state is unavailable; writes are blocked.", deny=True)


def known_prefixes(config: dict) -> tuple[str, ...]:
    """Only the exact environment namespace may use this package's policy state."""
    return (f"mcp__{config['server_name']}__",)


def inventory_tools() -> frozenset[str]:
    try:
        inventory = json.loads((Path(__file__).parent / "tools.json").read_text())["tools"]
        return frozenset(inventory) if isinstance(inventory, dict) else frozenset()
    except (OSError, ValueError, KeyError, TypeError):
        return frozenset()


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError
        result = handle(event)
    except (ValueError, TypeError):
        result = output("PreToolUse", "Malformed Pai hook event JSON.", deny=True)
    if result is not None:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
