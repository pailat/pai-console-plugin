"""Shared helpers of the pai-harness hooks: the hook event, the harness role, the config and the state dir. Stdlib only.

With no PAI_HARNESS_ROLE in the environment every hook does nothing. Hooks print one JSON object on stdout, or
nothing to let the event through. They only allow or deny, never ask.
"""
from __future__ import annotations

import json
import os
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from harness_config import ConfigError, find_config, load_file  # noqa: E402


def git(root: Path, *args: str) -> str | None:
    """Stdout of `git -C root ARGS`, or None when git is missing, fails or times out. The one git helper of the hooks."""
    try:
        done = run_process(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=8)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def toplevel(path: Path) -> Path | None:
    """The real git toplevel of path, or None outside a work tree."""
    top = (git(path, "rev-parse", "--show-toplevel") or "").strip()
    return Path(os.path.realpath(top)) if top else None


def in_repository(path: Path) -> bool:
    """True when path, or the nearest existing ancestor, sits under a directory holding a `.git` entry. Tells a git lookup that
    failed (fail closed) from a path that is not in any repository (left alone)."""
    here = Path(os.path.realpath(path))
    while not here.exists() and here != here.parent:
        here = here.parent
    return any((d / ".git").exists() for d in (here, *here.parents))


def common_dir(path: Path) -> Path | None:
    """The real git common directory (shared by every worktree of a repository) of path, or None when the lookup fails."""
    found = (git(path, "rev-parse", "--git-common-dir") or "").strip()
    if not found:
        return None
    candidate = Path(found)
    return Path(os.path.realpath(candidate if candidate.is_absolute() else path / candidate))


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
