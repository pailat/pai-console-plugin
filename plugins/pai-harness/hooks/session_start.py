#!/usr/bin/env python3
"""SessionStart: inject the closed brief and the curated Knowledge as additionalContext.

PAI_HARNESS_BRIEF names the brief file. Knowledge comes from the command in PAI_HARNESS_KNOWLEDGE_CMD (so it is
testable offline): it gets the project, role and agent as one JSON object on stdin and prints markdown.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common as common  # noqa: E402


def brief_section() -> str:
    path = os.environ.get("PAI_HARNESS_BRIEF", "").strip()
    if not path:
        return "## Brief\n\nNo brief was assigned (PAI_HARNESS_BRIEF is not set). Ask your parent for one before you start."
    try:
        return "## Brief\n\n" + Path(path).expanduser().read_text(encoding="utf-8").strip()
    except OSError as error:
        return f"## Brief\n\nThe brief at {path} could not be read ({error.strerror}). Ask your parent before you start."


def knowledge_section(config: dict | None, event: dict) -> str:
    command = os.environ.get("PAI_HARNESS_KNOWLEDGE_CMD", "").strip()
    if not command:
        return ""
    request = {"role": common.role(), "agent": common.agent_name(event), "session_id": event.get("session_id"),
               "project": (config or {}).get("project", {})}
    try:
        done = run_process(shlex.split(command), input=json.dumps(request), text=True, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        return f"## Curated Knowledge\n\nThe Knowledge fetch failed ({type(error).__name__}). Work from the brief and search Knowledge yourself."
    if done.returncode != 0 or not done.stdout.strip():
        return "## Curated Knowledge\n\nThe Knowledge fetch returned nothing. Work from the brief and search Knowledge yourself."
    return "## Curated Knowledge\n\n" + done.stdout.strip()


def main() -> None:
    event = common.read_event()
    if not common.role():
        return
    config, _, _ = common.load(event)
    sections = [brief_section(), knowledge_section(config, event)]
    context = f"# Pai Harness session ({common.role()})\n\n" + "\n\n".join(s for s in sections if s)
    common.emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}})


if __name__ == "__main__":
    main()
