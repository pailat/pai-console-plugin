#!/usr/bin/env python3
"""Stop: a session may not stop without a valid knowledge delta.

A delta is the JSON marker <state dir>/deltas/<agent>.json with a non-empty "nodes" list of node references
(ids or slugs of the Knowledge nodes the session created or changed). The distiller writes it. The agent name
is PAI_HARNESS_AGENT, else the session id.

The block is bounded so a `claude -p` run can never loop: after MAX_BLOCKS blocks (counted in <state dir>/deltas/<agent>.blocks)
the next stop is allowed and a `.missing` marker is written next to the delta marker, for the parent to see.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common as common  # noqa: E402


def delta_path(state: Path, name: str) -> Path:
    return state / "deltas" / f"{name}.json"


MAX_BLOCKS = 3


def count_path(state: Path, name: str) -> Path:
    return state / "deltas" / f"{name}.blocks"


def missing_path(state: Path, name: str) -> Path:
    return state / "deltas" / f"{name}.missing"


def blocks_so_far(path: Path) -> int:
    try:
        return max(0, int(path.read_text(encoding="utf-8").strip()))
    except (OSError, ValueError):
        return 0


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
    counter = count_path(state, name)
    if not problem:
        counter.unlink(missing_ok=True)
        missing_path(state, name).unlink(missing_ok=True)
        return
    blocks = blocks_so_far(counter)
    if blocks >= MAX_BLOCKS:
        marker = {"agent": name, "blocks": blocks, "problem": problem, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        try:
            missing_path(state, name).write_text(json.dumps(marker) + "\n", encoding="utf-8")
        except OSError:
            pass  # still allow the stop: the bound matters more than the marker
        return
    try:
        counter.parent.mkdir(parents=True, exist_ok=True)
        counter.write_text(f"{blocks + 1}\n", encoding="utf-8")
    except OSError:
        return  # cannot count, so cannot bound: allow rather than risk a loop
    common.emit({"decision": "block", "reason": (
        f"You cannot stop yet: a knowledge delta is required and {problem}. Distill what this session "
        f"learned into Pai Knowledge (search first, decisions as proposals, real sources), then write {path} as "
        '{"nodes": ["<node id or slug>", ...]} with at least one node you created or changed.')})


if __name__ == "__main__":
    main()
