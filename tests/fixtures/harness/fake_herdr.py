#!/usr/bin/env python3
"""Fake `herdr` for the harness tests: logs argv; `pane run` executes the command in a shell, `wait-output` succeeds."""
import json
import os
import subprocess
import sys

with open(os.environ["FAKE_HERDR_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\n")
if sys.argv[1:3] == ["pane", "run"]:
    sys.exit(subprocess.run(sys.argv[4], shell=True).returncode and 0)
sys.exit(0)
