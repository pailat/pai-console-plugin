#!/usr/bin/env python3
"""Stop: a session may not stop without a valid knowledge delta.

A delta is the JSON marker <state dir>/deltas/<agent>.json with a non-empty "nodes" list of node references
(ids or slugs of the Knowledge nodes the session created or changed). The distiller writes it. The agent name
is PAI_HARNESS_AGENT, else the session id.

The block is bounded so a `claude -p` run can never loop: after MAX_BLOCKS blocks (counted in <state dir>/deltas/<agent>.blocks)
the next stop is allowed and a `.missing` marker is written next to the delta marker, for the parent to see.

A saved report (<agent>.report.json from `delta_marker.py report`, a read-only token) is not a delta: the block and the `.missing` reason
become `knowledge write blocked: read-only token`; the 3-block bound is unchanged.

The stop is also blocked while the worktree holds changes outside the agent's zones (see zone_diff.py): that covers
the writes PreToolUse cannot see (`sed -i`, `cp`, `mv`, python or node scripts). The block names the zone owner. It shares
the same bound; the `.missing` marker then also lists the out-of-zone paths.

A writing role (harness_lib.WRITING_ROLES: implementer, mechanical, integrator) with no zone assigned is blocked too: with
no zone the diff above checks nothing, so that would fail open. The block text is "no write zone configured for ROLE; ask
your lead", inside the same bound. Non-writing roles may run zoneless.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common as common  # noqa: E402
import pre_tool_use as zones  # noqa: E402
import zone_diff  # noqa: E402
from harness_lib import WRITING_ROLES  # noqa: E402


def delta_path(state: Path, name: str) -> Path:
    return state / "deltas" / f"{name}.json"


MAX_BLOCKS = 3
MAX_LISTED = 10  # paths named in the block text; a long list once overflowed the run's context


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


READ_ONLY_REASON = "knowledge write blocked: read-only token"


def report_path(state: Path, name: str) -> Path:
    return state / "deltas" / f"{name}.report.json"


def main() -> None:
    event = common.read_event()
    if not common.role():
        return
    config, config_path, _ = common.load(event)
    state = common.state_dir(config)
    if state is None:
        return
    name = common.agent_name(event)
    if not name:
        return
    path = delta_path(state, name)
    problem = valid_delta(path)
    report = bool(problem) and report_path(state, name).is_file()  # a saved report is not a delta: it names why none exists
    if report:
        problem = READ_ONLY_REASON
    zoneless = ""
    if config is not None and common.role() in WRITING_ROLES and not zones.my_zones(config, name):
        zoneless = f"no write zone configured for {common.role()}; ask your lead"
    flagged = zone_diff.out_of_zone(config, config_path, state, name, Path(event.get("cwd") or os.getcwd())) if config is not None and config_path is not None else []
    counter = count_path(state, name)
    if not problem and not flagged and not zoneless:
        counter.unlink(missing_ok=True)
        missing_path(state, name).unlink(missing_ok=True)
        return
    blocks = blocks_so_far(counter)
    unchecked = any(zone_diff.is_unchecked(reason) for _, reason in flagged)  # an unreadable zone diff is never waved through by the bound
    if blocks >= MAX_BLOCKS:
        marker = {"agent": name, "blocks": blocks, "problem": problem or zoneless or "changes outside the agent's zones",
                  "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        if zoneless:
            marker["zoneless"] = zoneless
        if flagged:
            marker["out_of_zone"] = [path_ for path_, _ in flagged]
        try:
            missing_path(state, name).write_text(json.dumps(marker) + "\n", encoding="utf-8")
        except OSError:
            pass  # still allow the stop: the bound matters more than the marker
        if not unchecked:
            return
    try:
        counter.parent.mkdir(parents=True, exist_ok=True)
        counter.write_text(f"{blocks + 1}\n", encoding="utf-8")
    except OSError:
        if not unchecked:
            return  # cannot count, so cannot bound: allow rather than risk a loop
    parts = []
    if report:
        parts.append(f"You cannot stop yet: {READ_ONLY_REASON}. {report_path(state, name)} is a report, not a delta. Stop with the BLOCKER "
                     "`knowledge write needs a project-scope write token` reported to your parent; never write a marker for nodes that were not written.")
    elif problem:
        parts.append(f"You cannot stop yet: a knowledge delta is required and {problem}. Distill what this session "
                     f"learned into Pai Knowledge (search first, decisions as proposals, real sources), then write {path} as "
                     '{"nodes": ["<node id or slug>", ...]} with at least one node you created or changed.')
    if zoneless:
        parts.append(("You cannot stop yet: " if not parts else "Also, ") + zoneless + ".")
    if flagged:
        lines = "\n".join(f"- {reason}" for _, reason in flagged[:MAX_LISTED])
        if len(flagged) > MAX_LISTED:
            lines += f"\n- ... and {len(flagged) - MAX_LISTED} more"
        total = f" ({len(flagged)} paths in all)" if len(flagged) > MAX_LISTED else ""
        parts.append(("You cannot stop yet: " if not parts else "Also, ") +
                     f"the worktree holds changes outside your zones{total} (sed -i, cp, mv and scripts are checked at Stop). "
                     f"Revert them or hand them to the zone owner:\n{lines}")
    common.emit({"decision": "block", "reason": "\n\n".join(parts)})


if __name__ == "__main__":
    main()
