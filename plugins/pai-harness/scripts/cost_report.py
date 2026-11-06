#!/usr/bin/env python3
"""Daily cost report from the run records (no model, stdlib only).

Usage: cost_report.sh [--config FILE] [--day YYYY-MM-DD | --all] [--json]
Reads <state dir>/runs/*.state.json and prints cost, turns, tokens and the cache-read share per day, per role and per model,
plus the cost per merged PR when --merged N is given. Runs without a recorded cost count as unpriced, never as zero.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402


def load_records(state: Path) -> list[dict]:
    records = []
    for path in sorted((state / "runs").glob("*.state.json")):
        record = lib.read_json(path)
        if isinstance(record, dict) and record.get("finished"):
            records.append(record)
    return records


def summarise(records: list[dict], key) -> dict:
    groups: dict = collections.defaultdict(lambda: {"runs": 0, "unpriced": 0, "cost_usd": 0.0, "turns": 0, "cache_read_tokens": 0,
                                                    "peak_context_tokens": 0, "failed": 0})
    for r in records:
        g = groups[key(r)]
        g["runs"] += 1
        g["failed"] += r.get("state") == "failed"
        if r.get("cost_usd") is None:
            g["unpriced"] += 1
        else:
            g["cost_usd"] += r["cost_usd"]
        g["turns"] += r.get("turns") or 0
        g["cache_read_tokens"] += r.get("cache_read_tokens") or 0
        g["peak_context_tokens"] = max(g["peak_context_tokens"], r.get("peak_context_tokens") or 0)
    return {k: {**v, "cost_usd": round(v["cost_usd"], 4)} for k, v in sorted(groups.items())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config")
    parser.add_argument("--day", help="UTC day to report (default: today)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--merged", type=int, help="merged PRs in the period, for cost per merged PR")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    config, _ = lib.load_config(args.config)
    state = lib.state_dir(config)
    day = args.day or lib.stamp()[:10]
    records = [r for r in load_records(state) if args.all or r["finished"].startswith(day)]
    report = {"day": "all" if args.all else day, "by_role": summarise(records, lambda r: r.get("role") or "unknown"),
              "by_model": summarise(records, lambda r: r.get("model") or "unknown"), "total": summarise(records, lambda r: "total").get("total", {})}
    if args.merged and report["total"]:
        report["cost_per_merged_pr_usd"] = round(report["total"]["cost_usd"] / args.merged, 4)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"cost report {report['day']}")
        for title in ("by_role", "by_model"):
            for name, g in report[title].items():
                print(f"  {title[3:]:5} {name:14} runs={g['runs']} failed={g['failed']} unpriced={g['unpriced']} usd={g['cost_usd']:.2f} turns={g['turns']} peak_ctx={g['peak_context_tokens']}")
        total = report["total"]
        print(f"  total usd={total.get('cost_usd', 0):.2f} runs={total.get('runs', 0)}" + (f" per_merged_pr={report['cost_per_merged_pr_usd']}" if "cost_per_merged_pr_usd" in report else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
