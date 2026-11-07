#!/usr/bin/env python3
"""Verify one mechanical-lane run: the diff touches ONLY the listed files and the project checks pass, else discard it and report.

Reads the run record written by `launch.sh --profile mechanical` (listed files, start commit, repo root, ignored-files baseline). The
verdict is `pass` only when the run is `done`, at least one listed file changed, no other path changed (tracked, staged, untracked or
gitignored) and every check exits 0. The scope is computed twice, before and AFTER the checks, because the checks run code in the
worktree. Anything else is a `discard`: the paths the run changed are restored to the start commit (untracked ones are removed), unless
--keep. HEAD moving away from the start commit is never undone here; it is reported.

Fail closed: any git failure, timeout or discard error writes a `discard` verdict (replacing any earlier one), prints a BLOCKER and exits 1.
The verdict carries the HEAD and a digest of the changed content; `task-done.sh` re-checks both before it closes the issue.

Sampling: every 5th passing run (a persistent counter in the state dir keyed by issue and run id, not a hash) is marked for a Sonnet review.
`--sample-every N` (1 to 5) can only add runs to that, never remove one. `task-done.sh` then needs a review file naming this run's digest (`--sample-reviewed FILE`).

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


def sample_slot(state: Path, key: str) -> int:  # raises ScopeError when the counter file is damaged
    """This run's place in the count of passing mechanical runs (key: issue and run id). Persistent and locked; a run keeps its slot when verified again."""
    path = state / "mechanical_samples.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with (state / "mechanical_samples.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        issues = {}
        if path.exists():  # a missing file is an empty history; an unreadable or malformed one is not (the caller samples the run)
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                issues = data["issues"]
                if not isinstance(issues, dict):
                    raise ValueError("issues is not a mapping")
            except (OSError, ValueError, KeyError, TypeError) as error:
                raise scope.ScopeError(f"the sampler counter is unreadable: {error}") from error
        if key not in issues:
            issues[key] = max([n for n in issues.values() if isinstance(n, int)] + [0]) + 1
            lib.write_json(path, {"passes": issues[key], "issues": issues})
        return issues[key]


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

    A path is acted on as itself (a symlink is removed, not followed). A gitignored file that existed before the run and was changed cannot be
    restored (it is not in git) and is reported. Only a clean "not in the start commit" answer from git leads to a removal.
    """
    base_root = Path(root).resolve()
    done: list[str] = []
    problems: list[str] = []
    for path in paths:
        try:
            if path.endswith("/"):
                problems.append(f"{path}: a dependency/cache directory changed; it is not in git and cannot be restored")
                continue
            full = base_root / path
            if base_root not in full.parent.resolve().parents and full.parent.resolve() != base_root:
                problems.append(f"{path}: its directory resolves outside the worktree, left alone")
                continue
            listed = scope.git(root, "ls-tree", "-z", "--name-only", base, "--", path)
            if listed.returncode != 0:
                problems.append(f"{path}: git ls-tree failed ({listed.returncode}): {listed.stderr.strip()}")
                continue
            if listed.stdout.strip("\0"):
                restored = scope.git(root, "restore", f"--source={base}", "--staged", "--worktree", "--", path)
                if restored.returncode != 0:
                    problems.append(f"{path}: git restore failed: {restored.stderr.strip()}")
                    continue
            elif path in baseline.get("files", {}):
                problems.append(f"{path}: an ignored file that existed before the run was changed; it cannot be restored from git")
                continue
            else:
                scope.git(root, "rm", "--cached", "-q", "--ignore-unmatch", "--", path)
                if os.path.lexists(full) and (full.is_symlink() or not full.is_dir()):
                    os.unlink(full)  # the path itself: a symlink is removed, never its target
            done.append(path)
        except (OSError, scope.ScopeError) as error:
            problems.append(f"{path}: {error}")
    return done, problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify-mechanical.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue")
    parser.add_argument("--check", action="append", default=[], help="a project check command, run in the worktree (repeatable)")
    parser.add_argument("--gate", action="append", default=[], help="a [gates] entry of the config to run as a check (repeatable)")
    parser.add_argument("--sample-every", type=int, default=SAMPLE_EVERY, help="also mark every N-th passing run (N 1 to 5) for a Sonnet review; every 5th is always marked, this only adds")
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
    head, digest, verify_baseline = "", "", ""
    baseline: dict = {}

    def measure(against: dict, tolerant: bool = False) -> dict:
        nonlocal changed, outside, head, digest
        now = scope.snapshot(root, base, against, tolerant, listed)
        changed, head, digest = now["changed"], now["head"], now["digest"]
        outside = [p for p in changed if p not in listed]
        return now["ignored"]

    def rescan_after_failure() -> None:
        """The post-check scan failed: rebuild head, changed and outside from fresh, independent reads; name whatever still cannot be read."""
        nonlocal changed, outside, head
        try:
            head = scope.head_of(root)
        except scope.ScopeError:
            head = ""
            problems.append("HEAD could not be read after the checks, so nothing is undone")
        try:
            changed = sorted(set(changed) | scope.tracked_and_untracked(root, base))
            outside = [p for p in changed if p not in listed]
        except scope.ScopeError:
            problems.append("tracked and untracked paths written by the checks could not be listed")
        try:
            sensitive_now = scope.ignored_diff(ignored_before, scope.ignored_state(root))
            changed = sorted(set(changed) | {p for p in sensitive_now if scope.sensitive(p) or p in listed})
            outside = [p for p in changed if p not in listed]
        except (scope.ScopeError, OSError):
            problems.append("the ignored files could not be scanned: a sensitive ignored file written by the checks may remain")
        if head and head != base:
            reasons.append(f"HEAD moved during the checks from {base[:12]} to {head[:12]}")

    ignored_before: dict = {}
    try:
        top, _ = scope.toplevel(root)
        if top != str(Path(root).resolve()):
            raise scope.ScopeError(f"the recorded worktree root {root} is not the repository root {top}")
        baseline = scope.read_baseline(record.get("ignored_baseline"))
        ignored_before = measure(baseline)
        if scope.git_integrity(root) != record.get("git_integrity"):
            reasons.append("git config, hooks or attributes under .git differ from launch (or were never recorded): the lane wrote there; inspect and restore them by hand")
        if record.get("state") != "done":
            reasons.append(f"the run is {record.get('state')}: {record.get('reason')}")
        if outside:
            reasons.append("changed outside the listed files: " + ", ".join(outside))
        if head != base:
            reasons.append(f"HEAD moved from {base[:12]} to {head[:12]}: commits are not undone here")
        if not outside and not [p for p in changed if p in listed]:
            reasons.append("no listed file changed")
        if not reasons and not args.dry_run:
            # The lane's own writes are vetted. What the checks write (caches, build output) is judged against the state right before them.
            before_checks = scope.write_state(state / "runs" / f"{issue}.ignored.verify.json", ignored_before)
            checks = run_checks(record["cwd"], commands)
            failed = [c for c in checks if c["exit_code"] != 0]
            if failed:
                reasons.append(f"check failed (exit {failed[0]['exit_code']}): {failed[0]['command']}")
            try:
                measure(ignored_before, tolerant=True)
                verify_baseline = str(before_checks)
                if outside:
                    reasons.append("changed outside the listed files after the checks: " + ", ".join(outside))
                if head != base:
                    reasons.append(f"HEAD moved during the checks from {base[:12]} to {head[:12]}")
                if scope.git_integrity(root) != record.get("git_integrity"):
                    reasons.append("the checks changed git config, hooks or attributes under .git: inspect and restore them by hand")
            except (scope.ScopeError, OSError, subprocess.SubprocessError) as error:
                reasons.append(f"could not measure the scope after the checks (fail closed), so it is unknown: {error}")
                rescan_after_failure()
    except (scope.ScopeError, OSError, subprocess.SubprocessError, KeyError) as error:
        reasons.append(f"could not establish the diff scope (fail closed): {error}")
    verdict = "discard" if reasons else ("unverified" if args.dry_run else "pass")
    if reasons and not (args.keep or args.dry_run):
        try:
            if changed and head == base:
                discarded, more = discard(root, base, changed, baseline)
                problems += more
        except Exception as error:  # noqa: BLE001 - a discard error must never prevent the verdict from being written
            problems.append(f"discard failed: {error}")
        if problems:
            reasons.append("could not undo everything: " + "; ".join(problems))
    sample_review, slot = False, None
    sample_key = f"{issue}:{record.get('run_id') or record.get('started')}"
    if verdict == "pass":
        earlier = record.get("verify") or {}
        try:
            slot = sample_slot(state, sample_key)
        except (scope.ScopeError, OSError) as error:
            slot = None  # fail closed: a damaged counter never loses a review. The run is sampled and the file is left as it is for the operator to inspect.
            print(f"{issue}: {error}; this run is marked for review", file=sys.stderr)
        # The constant rule decides; --sample-every and an earlier sampled verdict of this same run can only add to it.
        sample_review = (slot is None or slot % SAMPLE_EVERY == 0 or slot % args.sample_every == 0
                         or bool(earlier.get("verdict") == "pass" and earlier.get("sample_key") == sample_key and earlier.get("sample_review")))
    result = {"issue": issue, "verdict": verdict, "reasons": reasons, "files": listed, "changed": changed, "outside": outside, "checks": checks,
              "discarded": discarded, "sample_review": sample_review, "sample_every": args.sample_every, "sample_slot": slot, "sample_key": sample_key,
              "base": base, "head": head, "digest": digest, "ignored_baseline": verify_baseline,
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
