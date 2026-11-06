"""Shared helpers of the pai-harness hooks: the hook event, the harness role, the config and the state dir. Stdlib only.

With no PAI_HARNESS_ROLE in the environment every hook does nothing. Hooks print one JSON object on stdout, or
nothing to let the event through. They only allow or deny, never ask.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from harness_config import ConfigError, find_config, load_file  # noqa: E402


def read_event() -> dict:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}
    return event if isinstance(event, dict) else {}


def role() -> str:
    return os.environ.get("PAI_HARNESS_ROLE", "").strip()


def agent_name(event: dict) -> str:
    return os.environ.get("PAI_HARNESS_AGENT", "").strip() or str(event.get("session_id") or "").strip()


def load(event: dict) -> tuple[dict | None, Path | None, str]:
    """Return (config, config path, error). The error is empty when the config loaded."""
    chosen = os.environ.get("PAI_HARNESS_CONFIG")
    try:
        path = Path(chosen) if chosen else find_config(Path(event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
        return load_file(path), path, ""
    except ConfigError as error:
        return None, None, str(error)


def state_dir(config: dict | None) -> Path | None:
    chosen = os.environ.get("PAI_HARNESS_STATE_DIR")
    if chosen:
        return Path(chosen)
    if config is None:
        return None
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return base / "pai-harness" / config["project"]["pai_project"]


def emit(payload: dict) -> None:
    print(json.dumps(payload))


def deny(reason: str) -> None:
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}})
