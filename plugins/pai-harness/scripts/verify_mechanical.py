#!/usr/bin/env python3
"""Verify one mechanical-lane run: the diff touches ONLY the listed files and the project checks pass, else discard it and report.

Reads the run record written by `launch.sh --profile mechanical` (listed files, start commit, worktree). The verdict is `pass` only when
the run is `done`, at least one listed file changed, no other path changed (tracked, staged or untracked) and every check exits 0.
Anything else is a `discard`: the paths the run changed are restored to the start commit (untracked ones are removed), unless
--keep. HEAD moving away from the start commit is never undone here; it is reported. A `pass` is also run through the deterministic
sampler: one run in five (--sample-every) is marked for a Sonnet review before the issue is closed. `task-done.sh` refuses a mechanical
run that has no `pass` verdict.

Usage: verify-mechanical.sh ISSUE (--check CMD ... | --gate NAME ...) [--sample-every N] [--keep] [--config FILE] [--dry-run]
Exit: 0 pass, 1 discard, 2 usage.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402

CHECK_TIMEOUT_SECONDS = 900
OUTPUT_TAIL_LINES = 15


def git(cwd: str, *argv: str, check: bool = False) -> subprocess.CompletedProcess:
    return run_process(["git", "-C", cwd, *argv], capture_output=True, text=True, timeout=60, check=check)


def changed_paths(cwd: str, base: str) -> list[str]:
    """Every path that differs from the start commit: tracked (staged or not, renames as both paths) and untracked."""
    tracked = git(cwd, "diff", "--name-only", "--no-renames", "-z", base)
    untracked = git(cwd, "ls-files", "--others", "--exclude-standard", "-z")
    if tracked.returncode != 0 or untracked.returncode != 0:
        raise RuntimeError("git could not list the changes: " + (tracked.stderr or untracked.stderr).strip())
    return sorted({p for p in (tracked.stdout + untracked.stdout).split("\0") if p})


def sampled(issue: str, base: str, every: int) -> bool:
    """The deterministic 1-in-N picker: a hash of the issue and the start commit, so the same run always gets the same answer."""
    return int(hashlib.sha256(f"{issue}:{base}".encode()).hexdigest()[:8], 16) % every == 0


def run_checks(cwd: str, commands: list[str]) -> list[dict]:
    """Run every command in the worktree, stop at the first failure; keep only the tail of the output."""
    results = []
    for command in commands:
        try:
            done = run_process(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=CHECK_TIMEOUT_SECONDS)
            code, text = done.returncode, (done.stdout + done.stderr)
        except subprocess.TimeoutExpired:
            code, text = 124, f"timeout after {CHECK_TIMEOUT_SECONDS}s"
        results.append({"command": command, "exit_code": code, "output_tail": "\n".join(text.strip().splitlines()[-OUTPUT_TAIL_LINES:])})
        if code != 0:
            break
    return results


def discard(cwd: str, base: str, paths: list[str]) -> list[str]:
    """Undo the run's changes path by path: restore what the start commit has, remove what it does not. Never touches any other path."""
    root = Path(cwd).resolve()
    done = []
    for path in paths:
        target = (root / path).resolve()
        if root not in target.parents:
            continue  # git only reports paths inside the worktree; refuse anything that resolves outside it
        if git(cwd, "cat-file", "-e", f"{base}:{path}").returncode == 0:
            git(cwd, "restore", f"--source={base}", "--staged", "--worktree", "--", path, check=True)
        else:
            git(cwd, "rm", "--cached", "-q", "--ignore-unmatch", "--", path)
            if target.is_file() or target.is_symlink():
                target.unlink()
        done.append(path)
    return done


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify-mechanical.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue")
    parser.add_argument("--check", action="append", default=[], help="a project check command, run in the worktree (repeatable)")
    parser.add_argument("--gate", action="append", default=[], help="a [gates] entry of the config to run as a check (repeatable)")
    parser.add_argument("--sample-every", type=int, default=5, help="mark one passing run in N for a Sonnet review (default 5)")
    parser.add_argument("--keep", action="store_true", help="report a discard but leave the changes in the worktree")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true", help="decide and print, but run no check, discard nothing and write no record")
    args = parser.parse_args(argv)
    config, _ = lib.load_config(args.config)
    issue = lib.issue_id(args.issue, config)
    state = lib.state_dir(config)
    state_file = state / "runs" / f"{issue}.state.json"
    record = lib.read_json(state_file)

    def usage(text: str) -> int:
        print(f"{issue}: {text}", file=sys.stderr)
        return lib.EXIT_USAGE

    if not record:
        return usage("no run recorded")
    if record.get("profile") != "mechanical" or not record.get("files") or not record.get("base") or not record.get("cwd"):
        return usage("not a mechanical-lane run (the record has no profile, files, base or cwd)")
    if args.sample_every < 1:
        return usage("--sample-every must be at least 1")
    commands = list(args.check)
    for name in args.gate:
        gate = config["gates"].get(name)
        if not isinstance(gate, list):
            return usage(f"--gate {name!r} is not a command gate in the config")
        commands += gate
    if not commands:
        return usage("name the project checks with --check or --gate: a run is never passed without them")

    cwd, base, listed = record["cwd"], record["base"], record["files"]
    reasons: list[str] = []
    changed: list[str] = []
    outside: list[str] = []
    checks: list[dict] = []
    try:
        changed = changed_paths(cwd, base)
        head = git(cwd, "rev-parse", "HEAD").stdout.strip()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        return usage(str(error))
    outside = [p for p in changed if p not in listed]
    if record.get("state") != "done":
        reasons.append(f"the run is {record.get('state')}: {record.get('reason')}")
    if outside:
        reasons.append("changed outside the listed files: " + ", ".join(outside))
    if head != base:
        reasons.append(f"HEAD moved from {base[:12]} to {head[:12]}: commits are not undone here")
    if not outside and not [p for p in changed if p in listed]:
        reasons.append("no listed file changed")
    if not reasons and not args.dry_run:
        checks = run_checks(cwd, commands)
        failed = [c for c in checks if c["exit_code"] != 0]
        if failed:
            reasons.append(f"check failed (exit {failed[0]['exit_code']}): {failed[0]['command']}")
    verdict = "discard" if reasons else "pass"
    discarded: list[str] = []
    if verdict == "discard" and changed and not (args.keep or args.dry_run) and head == base:
        discarded = discard(cwd, base, changed)
    result = {"issue": issue, "verdict": verdict, "reasons": reasons, "files": listed, "changed": changed, "outside": outside, "checks": checks,
              "discarded": discarded, "sample_review": verdict == "pass" and sampled(issue, base, args.sample_every), "sample_every": args.sample_every,
              "model": record.get("model"), "cost_usd": record.get("cost_usd"), "turns": record.get("turns"), "verified": lib.stamp()}
    if args.dry_run:
        lib.show({**result, "dry_run": True})
        return 0 if verdict == "pass" else lib.EXIT_FAILED
    lib.write_json(state_file, {**record, "verify": result})
    lib.emit(state, "run.verified", {k: result[k] for k in ("issue", "verdict", "reasons", "sample_review")})
    lib.show(result)
    if verdict == "pass":
        sample = ", sample-eligible: SONNET REVIEW REQUIRED" if result["sample_review"] else ""
        print(f"RESULT {issue} done: check pass{sample}", file=sys.stderr)
        return 0
    print(f"BLOCKER {issue}: mechanical run discarded: {'; '.join(reasons)}", file=sys.stderr)
    return lib.EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
