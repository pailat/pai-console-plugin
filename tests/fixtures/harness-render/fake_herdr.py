#!/usr/bin/env python3
"""Fake `herdr` for the render tests: logs every argv as JSON, answers `pane get` and `tab create` like Herdr, runs `pane run` in a shell."""
import json
import os
import subprocess
import sys

argv = sys.argv[1:]
with open(os.environ["FAKE_HERDR_LOG"], "a") as log:
    log.write(json.dumps(argv) + "\n")
if os.environ.get("FAKE_HERDR_FAIL") == "1" and argv[0] in ("tab", "workspace"):  # the display commands fail; pane commands keep working
    sys.exit(1)
if argv[:2] == ["pane", "get"]:
    print(json.dumps({"id": "cli:pane:get", "result": {"type": "pane_info", "pane": {"pane_id": argv[2], "tab_id": "wAC:t2", "workspace_id": "wAC"}}}))
elif argv[:2] == ["tab", "create"]:
    print(json.dumps({"id": "cli:tab:create", "result": {"type": "tab_created", "tab": {"tab_id": "wAC:t3", "workspace_id": "wAC"}, "root_pane": {"pane_id": "wAC:p9", "tab_id": "wAC:t3"}}}))
elif argv[:2] == ["pane", "run"]:
    subprocess.run(argv[3], shell=True)
sys.exit(0)
