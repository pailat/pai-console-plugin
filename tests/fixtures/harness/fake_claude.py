#!/usr/bin/env python3
"""Fake `claude` for the harness tests: prints a fixture as stream-json, records its argv and stdin, exits as told.

FAKE_CLAUDE_FIXTURE: fixture file. FAKE_CLAUDE_EXIT: exit code (default 0). FAKE_CLAUDE_LOG: where to write argv and the prompt.
FAKE_CLAUDE_RUN_HELPER: run the --mcp-config headersHelper and record its rc and header keys (not the value).
FAKE_CLAUDE_SLEEP: seconds to sleep after the output (timeout tests).
"""
import json
import os
import sys
import time

if "--help" in sys.argv[1:]:  # the launcher probes for --restricted; FAKE_CLAUDE_NO_RESTRICTED simulates an old claude
    sys.stdout.write("Usage: claude [options]\n  --model <model>\n" + ("" if os.environ.get("FAKE_CLAUDE_NO_RESTRICTED") else "  --restricted   Restricted mode\n"))
    sys.exit(0)
prompt = sys.stdin.read()
log = os.environ.get("FAKE_CLAUDE_LOG")
if log:
    with open(log, "w") as handle:
        json.dump({"argv": sys.argv[1:], "prompt": prompt, "env": sorted(os.environ)}, handle)
if os.environ.get("FAKE_CLAUDE_RUN_HELPER") and "--mcp-config" in sys.argv:
    # Like Claude Code: run the server's headersHelper through a shell. Record only its exit code and the header's shape, never its value.
    import subprocess
    entry = json.load(open(sys.argv[sys.argv.index("--mcp-config") + 1]))["mcpServers"]["pai"]
    done = subprocess.run(entry["headersHelper"], shell=True, capture_output=True, text=True)
    try:
        shape = sorted(json.loads(done.stdout))
    except ValueError:
        shape = None
    with open(os.environ["FAKE_CLAUDE_LOG"] + ".helper", "w") as handle:
        json.dump({"rc": done.returncode, "keys": shape, "stdout_empty": not done.stdout.strip()}, handle)
with open(os.environ["FAKE_CLAUDE_FIXTURE"]) as fixture:
    sys.stdout.write(fixture.read())
sys.stdout.flush()
time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "0")))
sys.exit(int(os.environ.get("FAKE_CLAUDE_EXIT", "0")))
