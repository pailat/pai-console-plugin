#!/usr/bin/env python3
"""Read ready lines and launch at most as many runs as the machine and queue limits allow.

A ready line is `ISSUE [queue=Q] [model=M] [role=R] [cwd=DIR] [prompt-file=FILE]`; blank lines and `#` lines are skipped.
Capacity = min(queue limit, machine max_agents (else limits.max_agents_per_machine), limits.max_agents) minus the
fresh running entries in that scope. Launches are detached unless --wait.

Usage: dispatcher.sh --queue Q [--ready FILE] [--wait] [--dry-run] [--config FILE]   (ready lines on stdin by default)
"""
from __future__ import annotations

import argparse
import os
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402

HERE = Path(__file__).resolve().parent


def parse_ready(text: str, config: dict, default_queue: str) -> list[dict]:
    items = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split()
        item = {"issue": lib.issue_id(parts[0], config), "queue": default_queue}
        for part in parts[1:]:
            key, _, value = part.partition("=")
            if key not in ("queue", "model", "role", "cwd", "prompt-file") or not value:
                print(f"{parts[0]}: ignoring {part!r}", file=sys.stderr)
                continue
            item[key] = value
        items.append(item)
    return items


def capacity(config: dict, state: Path, queue: str) -> tuple[int, dict]:
    live = lib.running(state)
    spec = config["queues"].get(queue, {})
    machine = spec.get("machine")
    limits = config["limits"]
    machine_cap = config["machines"].get(machine or "", {}).get("max_agents", limits["max_agents_per_machine"])
    queue_cap = spec.get("limit", limits["max_agents"])
    used = {"total": len(live), "queue": sum(1 for e in live if e.get("queue") == queue),
            "machine": sum(1 for e in live if machine and e.get("machine") == machine)}
    room = min(limits["max_agents"] - used["total"], queue_cap - used["queue"], machine_cap - (used["machine"] if machine else used["total"]))
    return max(room, 0), {"used": used, "queue_limit": queue_cap, "machine_limit": machine_cap, "machine": machine}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dispatcher.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--ready", help="file of ready lines (default: stdin)")
    parser.add_argument("--wait", action="store_true", help="run launches one after another and wait for each")
    parser.add_argument("--config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config, config_path = lib.load_config(args.config)
    if args.queue not in config["queues"]:
        print(f"unknown queue {args.queue!r} (declare it in [queues])", file=sys.stderr)
        return lib.EXIT_USAGE
    state = lib.state_dir(config)
    ready = parse_ready(Path(args.ready).read_text(encoding="utf-8") if args.ready else sys.stdin.read(), config, args.queue)
    room, detail = capacity(config, state, args.queue)
    busy = {e["name"] for e in lib.running(state)}
    plan = {"launch": [], "skipped": []}
    for item in ready:
        if item["issue"] in busy:
            plan["skipped"].append({"issue": item["issue"], "why": "already running"})
        elif item["queue"] != args.queue:
            plan["skipped"].append({"issue": item["issue"], "why": f"belongs to queue {item['queue']}"})
        elif not item.get("prompt-file"):
            plan["skipped"].append({"issue": item["issue"], "why": "no prompt-file"})
        elif len(plan["launch"]) >= room:
            plan["skipped"].append({"issue": item["issue"], "why": "no capacity"})
        else:
            plan["launch"].append(item)
    lib.show({"dry_run": args.dry_run, "capacity": room, **detail, **plan})
    if args.dry_run:
        return 0
    for item in plan["launch"]:
        command = [sys.executable, str(HERE / "launch.py"), item["issue"], "--prompt-file", item["prompt-file"], "--queue", args.queue,
                   "--config", str(config_path)]
        if os.environ.get("PAI_HARNESS_PARENT"):
            command += ["--parent", os.environ["PAI_HARNESS_PARENT"]]  # the agent woken when the run ends; launch.py refuses a pane run without one
        for key in ("model", "role", "cwd"):
            if key in item:
                command += [f"--{key}", item[key]]
        if args.wait:
            run_process(command)
        else:
            # Register before detaching so the next dispatch pass counts this run even before claude starts.
            lib.register(state, item["issue"], state="running", queue=args.queue, machine=detail["machine"])
            subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lib.emit(state, "dispatch", {"queue": args.queue, "launched": [i["issue"] for i in plan["launch"]]}) if plan["launch"] else None
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
