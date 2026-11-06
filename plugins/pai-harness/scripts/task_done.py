#!/usr/bin/env python3
"""Close a task from its recorded run: only a `done` run (stream result success and exit code 0) can be closed.

Marks the registry entry done, emits `task.done`, and prints the three-line status. A failed or blocked run exits with
its code (1 failed, 3 blocked) and changes nothing, so the lead sees the reason instead of a false close.

Usage: task-done.sh ISSUE [--config FILE] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402
from linear_status import compose, from_run  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="task-done.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config, _ = lib.load_config(args.config)
    issue = lib.issue_id(args.issue, config)
    state = lib.state_dir(config)
    record = lib.read_json(state / "runs" / f"{issue}.state.json")
    if not record:
        print(f"{issue}: no run recorded", file=sys.stderr)
        return lib.EXIT_USAGE
    print(compose(*from_run(record)))
    if record["state"] != "done":
        print(f"{issue}: not closed, run is {record['state']}: {record['reason']}", file=sys.stderr)
        return lib.exit_for(record["state"])
    if not args.dry_run:
        lib.register(state, issue, state="done")
        lib.emit(state, "task.done", {"issue": issue, "session_id": record.get("session_id"), "cost_usd": record.get("cost_usd"), "turns": record.get("turns")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
