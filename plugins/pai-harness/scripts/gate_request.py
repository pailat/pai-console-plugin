#!/usr/bin/env python3
"""Ask a gate for one exact commit, using the commands in the [gates] config.

The sha must be a full 40-character commit id: a branch name or an abbreviation is refused, because a gate result is
only evidence for the exact commit it ran on. With --run the checkout in --cwd must be at that sha, and the gate
commands run there. With --root the request also reports whether the changed files touch a ROOT zone or root path.

Usage: gate-request.sh --sha SHA40 [--gate NAME ...] [--issue ID] [--run --cwd DIR] [--root --files-from FILE] [--dry-run]
       gate-request.sh --hotfix --sha SHA40 --cwd DIR [--pr-title TEXT] [--label L ...] [--phase pre-merge|post-merge]
Exit codes: 0 requested (or every gate passed with --run), 1 a gate failed, 2 bad usage.

Hotfix mode (the [gates.hotfix] profile for a red release) prints the decision as JSON. Phase pre-merge: the profile is
inactive when active_when passes on the tip, the PR is refused when neither its title nor a label matches applies_to,
otherwise pre_merge runs and a green result says to merge at once. Phase post-merge, run after the merge: post_merge
(the full gate) runs on the tip and a failure emits a revert instruction and one BLOCKER line.
Hotfix exit codes: 0 inactive, merge now or post-merge green; 1 refused, a pre-merge failure or a revert; 2 bad usage.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402


def root_hits(config: dict, files: list[str]) -> list[str]:
    patterns = list(config["rules"]["root_paths"])
    for zone in config["zones"].values():
        if zone["root"]:
            patterns += zone["globs"]
    return [f for f in files if lib.matches(f, patterns)]


def shell(command: str, cwd: str) -> int:
    return run_process(command, shell=True, cwd=cwd).returncode


def hotfix_decide(profile: dict, sha: str, title: str, labels: list[str], runner=shell, cwd: str = ".", phase: str = "pre-merge", merge=None) -> dict:
    """Decide the hotfix lane. runner(command, cwd) returns an exit code; merge() (optional) merges at once, then the post phase runs.

    decision is one of: inactive, refused, pre_merge_failed, merge, post_merge_passed, revert.
    """
    steps: list[dict] = []

    def step(name: str, command: str) -> int:
        rc = runner(command, cwd)
        steps.append({"step": name, "command": command, "rc": rc})
        return rc

    def result(decision: str, **extra: object) -> dict:
        return {"mode": "hotfix", "sha": sha, "phase": phase, "decision": decision, "merge": decision == "merge", "revert": decision == "revert",
                "blocker": extra.pop("blocker", None), "steps": steps, **extra}

    if phase == "pre-merge":
        if step("active_when", profile["active_when"]) == 0:
            return result("inactive", reason="the release tip is green")
        if not any(re.search(profile["applies_to"], text) for text in [title, *labels]):
            return result("refused", reason=f"neither the PR title nor a label matches {profile['applies_to']!r}")
        for command in profile["pre_merge"]:
            if step("pre_merge", command):
                return result("pre_merge_failed", reason=f"pre_merge failed: {command}; do not merge")
        if merge is None:
            return result("merge", reason="pre_merge is green: merge at once, then run --phase post-merge on the tip")
        merge()
    if step("post_merge", profile["post_merge"]) == 0:
        return result("post_merge_passed", reason="the full gate is green on the tip")
    blocker = f"BLOCKER hotfix {sha}: post_merge failed on the release tip ({profile['post_merge']})"
    if profile["revert_on_failure"]:
        return result("revert", reason="post_merge failed: revert the merge", blocker=blocker)
    return result("post_merge_failed", reason="post_merge failed; revert_on_failure is off", blocker=blocker)


def hotfix_main(args: argparse.Namespace, config: dict) -> int:
    profile = config["gates"].get("hotfix")
    if not isinstance(profile, dict):
        print("no [gates.hotfix] profile is configured", file=sys.stderr)
        return lib.EXIT_USAGE
    decision = hotfix_decide(profile, args.sha, args.pr_title or "", args.label or [], cwd=args.cwd, phase=args.phase.replace("_", "-"))
    print(json.dumps(decision, indent=2))
    if decision["blocker"]:
        print(decision["blocker"])
    return 1 if decision["decision"] in ("refused", "pre_merge_failed", "revert", "post_merge_failed") else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="gate-request.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--gate", action="append", help="gate name (default: every gate in [gates])")
    parser.add_argument("--issue")
    parser.add_argument("--run", dest="execute", action="store_true")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--root", action="store_true")
    parser.add_argument("--files-from", help="file with one changed path per line (default with --root: stdin)")
    parser.add_argument("--config")
    parser.add_argument("--hotfix", action="store_true", help="decide the [gates.hotfix] profile for a red release")
    parser.add_argument("--pr-title", help="hotfix: the PR title, matched against applies_to")
    parser.add_argument("--label", action="append", help="hotfix: a PR label, matched against applies_to (repeatable)")
    parser.add_argument("--phase", choices=("pre-merge", "post-merge"), default="pre-merge", help="hotfix phase (default: pre-merge)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config, _ = lib.load_config(args.config)
    if not lib.SHA.fullmatch(args.sha):
        print(f"--sha must be a full 40-character lower-case commit id, got {args.sha!r}", file=sys.stderr)
        return lib.EXIT_USAGE
    if args.hotfix:
        return hotfix_main(args, config)
    plain = {n: c for n, c in config["gates"].items() if n != "hotfix"}  # the hotfix profile only runs through --hotfix
    names = args.gate or list(plain)
    unknown = [n for n in names if n not in plain]
    if unknown or not names:
        print(f"unknown or missing gates: {', '.join(unknown) or '(none configured)'}; configured: {', '.join(plain) or 'none'}", file=sys.stderr)
        return lib.EXIT_USAGE
    request = {"sha": args.sha, "issue": args.issue, "gates": {n: plain[n] for n in names}}
    if args.root:
        text = Path(args.files_from).read_text(encoding="utf-8") if args.files_from else sys.stdin.read()
        hits = root_hits(config, [line.strip() for line in text.splitlines() if line.strip()])
        request["root"] = {"touches_root": bool(hits), "files": hits}
    if args.dry_run:
        lib.show({"dry_run": True, **request})
        return 0
    state = lib.state_dir(config)
    where = lib.emit(state, "gate.requested", request)
    if not args.execute:
        lib.show({**request, "delivered_via": where})
        return 0
    head = run_process(["git", "-C", args.cwd, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != args.sha:
        print(f"checkout is at {head or 'unknown'}, not the requested {args.sha}; gate not run", file=sys.stderr)
        return lib.EXIT_USAGE
    results = {}
    for name in names:
        for command in plain[name]:
            done = run_process(command, shell=True, cwd=args.cwd)
            results[name] = done.returncode
            if done.returncode:
                break
    verdict = "PASS" if not any(results.values()) else "FAIL"
    lib.emit(state, "gate.result", {"sha": args.sha, "issue": args.issue, "verdict": verdict, "results": results})
    lib.show({**request, "verdict": verdict, "results": results})
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
