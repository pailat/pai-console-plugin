#!/usr/bin/env python3
"""Fake `herdr` with pane tokens: `pane report-metadata` stores them, `agent start` registers an agent, `agent list` reports both.

State lives in FAKE_HERDR_STATE (JSON). FAKE_HERDR_START_FAIL=1 fails `agent start`; FAKE_HERDR_TAG_FAIL=1 fails `report-metadata`.
FAKE_HERDR_START_NOT_READY=1 registers the agent but exits 1 (agent_not_ready: running, blocked at a dialog). FAKE_HERDR_DROP_TOKENS=1 makes `agent list` show no tokens.
FAKE_HERDR_AGENTS (JSON list of {name, pane_id, tokens}) seeds agents. Every argv is logged to FAKE_HERDR_LOG.
"""
import json
import os
import sys

argv = sys.argv[1:]
with open(os.environ["FAKE_HERDR_LOG"], "a") as log:
    log.write(json.dumps(argv) + "\n")
path = os.environ["FAKE_HERDR_STATE"]
try:
    state = json.load(open(path))
except OSError:
    state = {"tokens": {}, "agents": json.loads(os.environ.get("FAKE_HERDR_AGENTS", "[]"))}


def save() -> None:
    json.dump(state, open(path, "w"))


if argv[:2] == ["pane", "report-metadata"]:
    if os.environ.get("FAKE_HERDR_TAG_FAIL") == "1":
        sys.exit(1)
    tokens = state["tokens"].setdefault(argv[2], {})
    for i, item in enumerate(argv):
        if item == "--token":
            k, _, v = argv[i + 1].partition("=")
            tokens[k] = v
    save()
elif argv[:2] == ["agent", "start"]:
    if os.environ.get("FAKE_HERDR_START_FAIL") == "1":
        sys.exit(1)
    state["agents"].append({"name": argv[2], "pane_id": argv[argv.index("--pane") + 1]})
    save()
    if os.environ.get("FAKE_HERDR_START_NOT_READY") == "1":
        print(json.dumps({"error": {"code": "agent_not_ready"}}))
        sys.exit(1)
elif argv[:2] == ["agent", "list"]:
    agents = [{**a, "tokens": a.get("tokens") or ({} if os.environ.get("FAKE_HERDR_DROP_TOKENS") == "1" else state["tokens"].get(a["pane_id"], {}))} for a in state["agents"]]
    print(json.dumps({"id": "cli:agent:list", "result": {"type": "agent_list", "agents": agents}}))
elif argv[:2] == ["pane", "get"]:
    print(json.dumps({"id": "cli:pane:get", "result": {"pane": {"pane_id": argv[2], "tab_id": "wAC:t2", "workspace_id": "wAC"}}}))
elif argv[:2] == ["pane", "run"]:
    import subprocess
    subprocess.run(argv[3], shell=True)
sys.exit(0)
