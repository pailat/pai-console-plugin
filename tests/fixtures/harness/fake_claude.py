#!/usr/bin/env python3
"""Fake `claude` for the harness tests: prints a fixture as stream-json, records its argv and stdin, exits as told.

FAKE_CLAUDE_FIXTURE: fixture file. FAKE_CLAUDE_EXIT: exit code (default 0). FAKE_CLAUDE_LOG: where to write argv and the prompt.
FAKE_CLAUDE_SLEEP: seconds to sleep after the output (timeout tests).
"""
import json
import os
import sys
import time

prompt = sys.stdin.read()
log = os.environ.get("FAKE_CLAUDE_LOG")
if log:
    with open(log, "w") as handle:
        json.dump({"argv": sys.argv[1:], "prompt": prompt}, handle)
with open(os.environ["FAKE_CLAUDE_FIXTURE"]) as fixture:
    sys.stdout.write(fixture.read())
sys.stdout.flush()
time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "0")))
sys.exit(int(os.environ.get("FAKE_CLAUDE_EXIT", "0")))
