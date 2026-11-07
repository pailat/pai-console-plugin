#!/usr/bin/env python3
"""Close a task from its recorded run: only a `done` run (stream result success and exit code 0) can be closed.

Marks the registry entry done, emits `task.done`, and prints the three-line status. A failed or blocked run exits with
its code (1 failed, 3 blocked) and changes nothing, so the lead sees the reason instead of a false close.

Usage: task-done.sh ISSUE [--sample-reviewed] [--config FILE] [--dry-run]

A mechanical-lane run closes only with a passing verify-mechanical.sh verdict that still matches the tree (same HEAD and same changed content),
and, when it was picked for the 1-in-5 sample, with --sample-reviewed REVIEW_FILE: a JSON file {"reviewer": "...", "verdict": "clean",
"diff_sha256": "<the digest in the verify verdict>"} written by the reviewer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402
from linear_status import compose, from_run  # noqa: E402
import mechanical_scope as scope  # noqa: E402


def stale_verdict(record: dict, verify: dict) -> str:
    """Why a passing verdict no longer holds for the tree as it is now, else ''. Fails closed on a git error.

    The digest covers the content of every path that differs from the start commit, so the work may have been committed since
    (HEAD a descendant of the start commit with the same net change) but nothing else may differ.
    """
    root = record.get("root") or record["cwd"]
    try:
        before = scope.read_baseline(verify.get("ignored_baseline"))
        now = scope.snapshot(root, record["base"], before, tolerant=True, listed=record.get("files"))
        if scope.git_integrity(root) != record.get("git_integrity"):
            return "git config, hooks or attributes under .git differ from launch"
        descends = now["head"] == record["base"] or scope.is_ancestor(root, record["base"], now["head"])
    except (scope.ScopeError, KeyError) as error:
        return f"the tree cannot be checked against the verdict ({error})"
    if not verify.get("digest") or now["digest"] != verify["digest"] or not descends:
        return "the worktree changed after the verdict (the changed content differs, or HEAD is no longer a descendant of the start commit)"
    return ""


def review_problem(path: str | None, verify: dict) -> str:
    """The review record must exist and name this run's diff digest. It is evidence, not a signature: the lead reads it."""
    if not path:
        return "no review record given"
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return f"review record unreadable: {error}"
    if not isinstance(data, dict) or not str(data.get("reviewer") or "").strip():
        return "the review record names no reviewer"
    if data.get("verdict") != "clean":
        return f"the review verdict is {data.get('verdict')!r}, not 'clean'"
    if data.get("diff_sha256") != verify.get("digest"):
        return "the review record is for a different diff (diff_sha256 does not match the verify verdict)"
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="task-done.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue")
    parser.add_argument("--config")
    parser.add_argument("--sample-reviewed", metavar="REVIEW_FILE", help="a mechanical run picked for sampling: the JSON review record (reviewer, verdict clean, diff_sha256 of this run's verify verdict)")
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
    if record.get("profile") == "mechanical":
        problem = stale_verdict(record, verify)
        if problem:
            print(f"{issue}: not closed, {problem}; run verify-mechanical.sh again", file=sys.stderr)
            return lib.EXIT_FAILED
        if verify.get("sample_review"):
            problem = review_problem(args.sample_reviewed, verify)
            if problem:
                print(f"{issue}: not closed, this run was picked for a Sonnet sample review ({problem}); review `git diff {record.get('base')}`, "
                      "write the review record, then rerun with --sample-reviewed REVIEW_FILE", file=sys.stderr)
                return lib.EXIT_FAILED
    if not args.dry_run:
        lib.register(state, issue, state="done")
        lib.emit(state, "task.done", {"issue": issue, "session_id": record.get("session_id"), "cost_usd": record.get("cost_usd"), "turns": record.get("turns")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
