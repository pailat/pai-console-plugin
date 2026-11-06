#!/usr/bin/env python3
"""Heartbeat and registry check.

Usage: health.sh beat NAME [--state S] | health.sh check [--stale-minutes N] [--now ISO] [--config FILE]
Exit codes of check: 0 every entry fresh, 1 at least one stale running entry, 2 empty registry or bad usage.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402


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
    lib.show({"checked_at": lib.stamp(at), "stale_after_minutes": args.stale_minutes, "entries": report})
    if not report:
        return lib.EXIT_USAGE
    return 1 if any(r["stale"] for r in report) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
