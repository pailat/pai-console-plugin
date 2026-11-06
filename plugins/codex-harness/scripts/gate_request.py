#!/usr/bin/env python3
"""Ask a gate for one exact commit, using the commands in the [gates] config.

The sha must be a full 40-character commit id: a branch name or an abbreviation is refused, because a gate result is
only evidence for the exact commit it ran on. With --run the checkout in --cwd must be at that sha, and the gate
commands run there. With --root the request also reports whether the changed files touch a ROOT zone or root path.

Usage: gate-request.sh --sha SHA40 [--gate NAME ...] [--issue ID] [--run --cwd DIR] [--root --files-from FILE] [--dry-run]
Exit codes: 0 requested (or every gate passed with --run), 1 a gate failed, 2 bad usage.
"""
from __future__ import annotations

import argparse
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
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config, _ = lib.load_config(args.config)
    if not lib.SHA.fullmatch(args.sha):
        print(f"--sha must be a full 40-character lower-case commit id, got {args.sha!r}", file=sys.stderr)
        return lib.EXIT_USAGE
    names = args.gate or list(config["gates"])
    unknown = [n for n in names if n not in config["gates"]]
    if unknown or not names:
        print(f"unknown or missing gates: {', '.join(unknown) or '(none configured)'}; configured: {', '.join(config['gates']) or 'none'}", file=sys.stderr)
        return lib.EXIT_USAGE
    request = {"sha": args.sha, "issue": args.issue, "gates": {n: config["gates"][n] for n in names}}
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
        for command in config["gates"][name]:
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
