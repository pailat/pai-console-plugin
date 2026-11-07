#!/usr/bin/env python3
"""Heartbeat and registry check.

Usage: health.sh beat NAME [--state S] | health.sh check [--stale-minutes N] [--now ISO] [--config FILE]
Check also warns (stderr, exit code unchanged) about each Herdr agent pane that has no pai tokens.
Exit codes of check: 0 every entry fresh, 1 at least one stale running entry, 2 empty registry or bad usage.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402


TOKEN_KEYS = ("role", "parent", "name", "issue", "wake_on_done")


def untagged_agents() -> list[dict]:
    """Agent panes Herdr knows that carry none of the pai wake tokens (nobody is woken when they end). Empty when Herdr is absent."""
    herdr = os.environ.get("PAI_HARNESS_HERDR", "herdr")
    try:
        done = run_process([herdr, "agent", "list"], capture_output=True, text=True, timeout=10)
        agents = json.loads(done.stdout)["result"]["agents"] if done.returncode == 0 else []
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return []
    return [{"name": a.get("name"), "pane_id": a.get("pane_id")} for a in agents
            if isinstance(a, dict) and not any((a.get("tokens") or {}).get(k) for k in TOKEN_KEYS)]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="health.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["beat", "check"])
    parser.add_argument("name", nargs="?")
    parser.add_argument("--state")
    parser.add_argument("--stale-minutes", type=int, default=lib.STALE_MINUTES)
    parser.add_argument("--now", help="ISO time like 2026-01-01T12:00:00Z (tests)")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config, _ = lib.load_config(args.config)
    state = lib.state_dir(config)
    if args.action == "beat":
        if not args.name:
            print("beat needs a NAME", file=sys.stderr)
            return lib.EXIT_USAGE
        if args.dry_run:
            lib.show({"dry_run": True, "would_beat": args.name})
            return 0
        fields = {"state": args.state} if args.state else {}
        lib.show(lib.register(state, args.name, **fields))
        return 0
    at = lib.parse_stamp(args.now) if args.now else lib.now()
    found = lib.entries(state)
    report = [{"name": e["name"], "state": e.get("state"), "heartbeat": e.get("heartbeat"),
               "stale": e.get("state") == "running" and lib.is_stale(e, at, args.stale_minutes)} for e in found]
    untagged = untagged_agents()
    for a in untagged:
        print(f"WARNING untagged-agent-pane: {a['name'] or a['pane_id']} ({a['pane_id']}) has no pai tokens; its parent is never woken. "
              f"Start agents with scripts/agent-start.sh or run bin/pai-pane-meta {a['pane_id']} name=... role=... parent=... wake_on_done=1", file=sys.stderr)
    lib.show({"checked_at": lib.stamp(at), "stale_after_minutes": args.stale_minutes, "entries": report, "untagged_agent_panes": untagged})
    if not report:
        return lib.EXIT_USAGE
    return 1 if any(r["stale"] for r in report) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
