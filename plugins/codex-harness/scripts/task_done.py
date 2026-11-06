#!/usr/bin/env python3
"""Close a task from its recorded run: only a `done` run (stream result success and exit code 0) can be closed.

Marks the registry entry done, emits `task.done`, and prints the three-line status. A failed or blocked run exits with
its code (1 failed, 3 blocked) and changes nothing, so the lead sees the reason instead of a false close.

Usage: task-done.sh ISSUE [--sample-reviewed] [--config FILE] [--dry-run]

A mechanical-lane run closes only with a passing verify-mechanical.sh verdict, and, when it was picked for the 1-in-5 sample, with --sample-reviewed.
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
    parser.add_argument("--sample-reviewed", action="store_true", help="a mechanical run picked for sampling: the Sonnet review of its diff is done and clean")
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
    verify = record.get("verify") or {}
    if record.get("profile") == "mechanical" and verify.get("verdict") != "pass":  # the lane closes only through verify-mechanical.sh
        print(f"{issue}: not closed, the mechanical run has no passing verify-mechanical.sh verdict ({verify.get('verdict') or 'not verified'})", file=sys.stderr)
        return lib.EXIT_FAILED
    if verify.get("sample_review") and not args.sample_reviewed:
        print(f"{issue}: not closed, this run was picked for a Sonnet sample review; review `git diff {record.get('base')}` then rerun with --sample-reviewed", file=sys.stderr)
        return lib.EXIT_FAILED
    if not args.dry_run:
        lib.register(state, issue, state="done")
        lib.emit(state, "task.done", {"issue": issue, "session_id": record.get("session_id"), "cost_usd": record.get("cost_usd"), "turns": record.get("turns")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
