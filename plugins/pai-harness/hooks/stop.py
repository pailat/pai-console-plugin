#!/usr/bin/env python3
"""Stop: a session may not stop without a valid knowledge delta.

A delta is the JSON marker <state dir>/deltas/<agent>.json with a non-empty "nodes" list of node references
(ids or slugs of the Knowledge nodes the session created or changed). The distiller writes it. The agent name
is PAI_HARNESS_AGENT, else the session id.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common as common  # noqa: E402


def delta_path(state: Path, name: str) -> Path:
    return state / "deltas" / f"{name}.json"


def valid_delta(path: Path) -> str:
    """Return "" for a valid delta, else the reason it is not."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "the marker file does not exist"
    except (OSError, json.JSONDecodeError):
        return "the marker file is not valid JSON"
    nodes = data.get("nodes") if isinstance(data, dict) else None
    if not isinstance(nodes, list) or not any(isinstance(n, str) and n.strip() for n in nodes):
        return 'the marker has no node reference in its "nodes" list'
    return ""


def main() -> None:
    event = common.read_event()
    if not common.role():
        return
    config, _, _ = common.load(event)
    state = common.state_dir(config)
    if state is None:
        return
    name = common.agent_name(event)
    if not name:
        return
    path = delta_path(state, name)
    problem = valid_delta(path)
    if problem:
        common.emit({"decision": "block", "reason": (
            f"You cannot stop yet: a knowledge delta is required and {problem}. Distill what this session "
            f"learned into Pai Knowledge (search first, decisions as proposals, real sources), then write {path} as "
            '{"nodes": ["<node id or slug>", ...]} with at least one node you created or changed.')})


if __name__ == "__main__":
    main()
