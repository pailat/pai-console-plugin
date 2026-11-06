#!/usr/bin/env python3
"""Verify one mechanical-lane run: the diff touches ONLY the listed files and the project checks pass, else discard it and report.

Reads the run record written by `launch.sh --profile mechanical` (listed files, start commit, repo root, ignored-files baseline). The
verdict is `pass` only when the run is `done`, at least one listed file changed, no other path changed (tracked, staged, untracked or
gitignored) and every check exits 0. The scope is computed twice, before and AFTER the checks, because the checks run code in the
worktree. Anything else is a `discard`: the paths the run changed are restored to the start commit (untracked ones are removed), unless
--keep. HEAD moving away from the start commit is never undone here; it is reported.

Fail closed: any git failure, timeout or discard error writes a `discard` verdict (replacing any earlier one), prints a BLOCKER and exits 1.
The verdict carries the HEAD and a digest of the changed content; `task-done.sh` re-checks both before it closes the issue.

Sampling: every 5th passing run (a persistent counter in the state dir, not a hash) is marked for a Sonnet review. `--sample-every` can only
make that stricter (1 to 5). `task-done.sh` then needs a review file naming this run's digest (`--sample-reviewed FILE`).

Usage: verify-mechanical.sh ISSUE (--check CMD ... | --gate NAME ...) [--sample-every N] [--keep] [--config FILE] [--dry-run]
Exit: 0 pass, 1 discard (or, with --dry-run, anything that is not a verified pass), 2 usage.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402
import mechanical_scope as scope  # noqa: E402

SAMPLE_EVERY = 5  # the contract: one passing mechanical run in five is reviewed. The CLI may only lower it.
CHECK_TIMEOUT_SECONDS = 900
OUTPUT_TAIL_LINES = 15


def sample_slot(state: Path, issue: str) -> int:
    """This issue's place in the count of passing mechanical runs. Persistent and locked; an issue keeps its slot when it is verified again."""
    path = state / "mechanical_samples.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with (state / "mechanical_samples.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            issues = data["issues"] if isinstance(data.get("issues"), dict) else {}
        except (OSError, ValueError, AttributeError):
            issues = {}
        if issue not in issues:
            issues[issue] = max([n for n in issues.values() if isinstance(n, int)] + [0]) + 1
            lib.write_json(path, {"passes": issues[issue], "issues": issues})
        return issues[issue]


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


def discard(root: str, base: str, paths: list[str], baseline: dict) -> tuple[list[str], list[str]]:
    """Undo the run's changes path by path: restore what the start commit has, remove what it does not. Returns (undone, problems); never raises.

    A gitignored file that existed before the run and was changed cannot be restored (it is not in git): it is reported as a problem.
    """
    base_root = Path(root).resolve()
    done: list[str] = []
    problems: list[str] = []
    for path in paths:
        try:
            target = (base_root / path).resolve()
            if base_root not in target.parents:
                problems.append(f"{path}: resolves outside the worktree, left alone")
                continue
            if scope.git(root, "cat-file", "-e", f"{base}:{path}").returncode == 0:
                restored = scope.git(root, "restore", f"--source={base}", "--staged", "--worktree", "--", path)
                if restored.returncode != 0:
                    problems.append(f"{path}: git restore failed: {restored.stderr.strip()}")
                    continue
            elif path in baseline:
                problems.append(f"{path}: an ignored file that existed before the run was changed; it cannot be restored from git")
                continue
            else:
                scope.git(root, "rm", "--cached", "-q", "--ignore-unmatch", "--", path)
                if target.is_file() or target.is_symlink():
                    target.unlink()
            done.append(path)
        except (OSError, scope.ScopeError) as error:
            problems.append(f"{path}: {error}")
    return done, problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify-mechanical.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue")
    parser.add_argument("--check", action="append", default=[], help="a project check command, run in the worktree (repeatable)")
    parser.add_argument("--gate", action="append", default=[], help="a [gates] entry of the config to run as a check (repeatable)")
    parser.add_argument("--sample-every", type=int, default=SAMPLE_EVERY, help="mark one passing run in N for a Sonnet review; N is 1 to 5 (default 5): it can only be made stricter")
    parser.add_argument("--keep", action="store_true", help="report a discard but leave the changes in the worktree")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true", help="decide and print the scope check, but run no check, discard nothing and write no record; the verdict is never `pass`")
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
    if not 1 <= args.sample_every <= SAMPLE_EVERY:
        return usage(f"--sample-every must be between 1 and {SAMPLE_EVERY}: the review rate can be made stricter, never looser")
    commands = list(args.check)
    for name in args.gate:
        gate = config["gates"].get(name)
        if not isinstance(gate, list):
            return usage(f"--gate {name!r} is not a command gate in the config")
        commands += gate
    if not commands:
        return usage("name the project checks with --check or --gate: a run is never passed without them")

    base, listed = record["base"], record["files"]
    root = record.get("root") or record["cwd"]
    reasons: list[str] = []
    changed: list[str] = []
    outside: list[str] = []
    checks: list[dict] = []
    discarded: list[str] = []
    problems: list[str] = []
    head, digest = "", ""
    baseline: dict = {}

    def measure() -> None:
        nonlocal changed, outside, head, digest
        now = scope.snapshot(root, base, record.get("ignored_baseline"))
        changed, head, digest = now["changed"], now["head"], now["digest"]
        outside = [p for p in changed if p not in listed]

    try:
        top, _ = scope.toplevel(root)
        if top != str(Path(root).resolve()):
            raise scope.ScopeError(f"the recorded worktree root {root} is not the repository root {top}")
        baseline = scope.read_baseline(record.get("ignored_baseline"))
        measure()
        if record.get("state") != "done":
            reasons.append(f"the run is {record.get('state')}: {record.get('reason')}")
        if outside:
            reasons.append("changed outside the listed files: " + ", ".join(outside))
        if head != base:
            reasons.append(f"HEAD moved from {base[:12]} to {head[:12]}: commits are not undone here")
        if not outside and not [p for p in changed if p in listed]:
            reasons.append("no listed file changed")
        if not reasons and not args.dry_run:
            checks = run_checks(record["cwd"], commands)
            failed = [c for c in checks if c["exit_code"] != 0]
            if failed:
                reasons.append(f"check failed (exit {failed[0]['exit_code']}): {failed[0]['command']}")
            measure()  # the checks ran code in the worktree: what they wrote counts too
            if outside:
                reasons.append("changed outside the listed files after the checks: " + ", ".join(outside))
            if head != base:
                reasons.append(f"HEAD moved during the checks from {base[:12]} to {head[:12]}")
    except (scope.ScopeError, OSError, subprocess.SubprocessError, KeyError) as error:
        reasons.append(f"could not establish the diff scope (fail closed): {error}")
    verdict = "discard" if reasons else ("unverified" if args.dry_run else "pass")
    if reasons and not (args.keep or args.dry_run):
        try:
            if changed and head == base:
                discarded, problems = discard(root, base, changed, baseline)
        except Exception as error:  # noqa: BLE001 - a discard error must never prevent the verdict from being written
            problems.append(f"discard failed: {error}")
        if problems:
            reasons.append("could not undo everything: " + "; ".join(problems))
    sample_review, slot = False, None
    if verdict == "pass":
        slot = sample_slot(state, issue)
        sample_review = slot % args.sample_every == 0
    result = {"issue": issue, "verdict": verdict, "reasons": reasons, "files": listed, "changed": changed, "outside": outside, "checks": checks,
              "discarded": discarded, "sample_review": sample_review, "sample_every": args.sample_every, "sample_slot": slot,
              "base": base, "head": head, "digest": digest,
              "model": record.get("model"), "cost_usd": record.get("cost_usd"), "turns": record.get("turns"), "verified": lib.stamp()}
    if args.dry_run:
        lib.show({**result, "dry_run": True})
        print(f"{issue}: dry run, {'would discard' if reasons else 'scope ok, checks NOT run'}: not a verified pass", file=sys.stderr)
        return lib.EXIT_FAILED
    lib.write_json(state_file, {**record, "verify": result})  # always replaces an earlier verdict, so a stale `pass` never survives
    lib.emit(state, "run.verified", {k: result[k] for k in ("issue", "verdict", "reasons", "sample_review")})
    lib.show(result)
    if verdict == "pass":
        sample = ", sample-eligible: SONNET REVIEW REQUIRED" if sample_review else ""
        print(f"RESULT {issue} done: check pass{sample}", file=sys.stderr)
        return 0
    print(f"BLOCKER {issue}: mechanical run discarded: {'; '.join(reasons)}", file=sys.stderr)
    return lib.EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
