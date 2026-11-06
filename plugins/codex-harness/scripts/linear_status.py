#!/usr/bin/env python3
"""Compose the three-line status comment for an issue, and post it only when a token is configured.

Lines: `Done: ...`, `Next: ...`, `Blocked: ...` (`none` when empty). With --from-run the lines come from the recorded run
state. The comment is printed unless the token env var (default LINEAR_API_KEY) and the endpoint env var
(LINEAR_API_URL, the GraphQL endpoint) are both set; then it is posted with commentCreate and also printed.

Usage: linear-status.sh ISSUE [--done T] [--next T] [--blocked T] [--from-run] [--token-env NAME] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402

MUTATION = "mutation($issueId: String!, $body: String!) { commentCreate(input: {issueId: $issueId, body: $body}) { success } }"


def compose(done: str, nxt: str, blocked: str) -> str:
    one = lambda text: " ".join((text or "").split()) or "none"  # noqa: E731 - keeps each field on one line
    return f"Done: {one(done)}\nNext: {one(nxt)}\nBlocked: {one(blocked)}"


def from_run(record: dict) -> tuple[str, str, str]:
    cost = f", cost ${record['cost_usd']:.4f}" if isinstance(record.get("cost_usd"), (int, float)) else ""
    summary = f"run {record['state']} in {record.get('turns') or '?'} turns{cost}, session {record.get('session_id') or 'unknown'}"
    if record["state"] == "done":
        return summary, "gate and review", "none"
    if record["state"] == "blocked":
        return summary, "grant the permission, then resume", record["reason"]
    return summary, "read the stream and relaunch or park", record["reason"]


def post(url: str, token: str, issue: str, body: str) -> None:
    payload = json.dumps({"query": MUTATION, "variables": {"issueId": issue, "body": body}}).encode()
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "Authorization": token})
    with urllib.request.urlopen(request, timeout=20) as reply:
        data = json.loads(reply.read())
    if data.get("errors") or not data.get("data", {}).get("commentCreate", {}).get("success"):
        raise RuntimeError("the endpoint refused the comment")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="linear-status.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue")
    parser.add_argument("--done", default="")
    parser.add_argument("--next", default="")
    parser.add_argument("--blocked", default="")
    parser.add_argument("--from-run", action="store_true")
    parser.add_argument("--token-env", default="LINEAR_API_KEY")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config, _ = lib.load_config(args.config)
    issue = lib.issue_id(args.issue, config)
    lines = (args.done, args.next, args.blocked)
    if args.from_run:
        record = lib.read_json(lib.state_dir(config) / "runs" / f"{issue}.state.json")
        if not record:
            print(f"{issue}: no run recorded", file=sys.stderr)
            return lib.EXIT_USAGE
        lines = from_run(record)
    text = compose(*lines)
    token, url = os.environ.get(args.token_env), os.environ.get("LINEAR_API_URL")
    if args.dry_run or not (token and url):
        print(text)
        return 0
    try:
        post(url, token, issue, text)
    except (OSError, RuntimeError, ValueError, urllib.error.URLError) as error:
        print(text)
        print(f"not posted: {type(error).__name__}", file=sys.stderr)
        return lib.EXIT_FAILED
    print(text)
    print("posted", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
