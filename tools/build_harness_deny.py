#!/usr/bin/env python3
"""Generate the pai-harness deny examples from plugins/pai-harness/scripts/deny_baseline.py (the single source). `--check` fails on drift."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "plugins/pai-harness/examples"
sys.path.insert(0, str(ROOT / "plugins/pai-harness/scripts"))
import deny_baseline  # noqa: E402

BASE_NOTE = ("Generic example for Acme. Copy into .claude/settings.json (project) or ~/.claude/settings.json (user). Deny rules hold in bypassPermissions "
             "and are the layer that stops Bash patterns and MCP writes, which the plugin hooks do not match today; launch.sh refuses to start a bypass run until the baseline is present. "
             "Patterns match the whole command with * as a wildcard; they are best effort, so keep the plugin hooks on as well. "
             "Merge and protected-branch denials are in settings.deny.non-merge.json: apply them to every role except the integrator and orchestrator.")
NON_MERGE_NOTE = ("Generic example for Acme. Add to the project settings of every role except the integrator and orchestrator (the roles that merge by design); "
                  "launch.sh requires these rules for every other role. Replace main, master and release/* with your protected branches.")


def files() -> dict[Path, str]:
    def dump(note: str, rules: list[str]) -> str:
        return json.dumps({"_comment": note, "permissions": {"deny": rules}}, indent=2) + "\n"
    return {EXAMPLES / "settings.deny.json": dump(BASE_NOTE, deny_baseline.example_rules()),
            EXAMPLES / "settings.deny.non-merge.json": dump(NON_MERGE_NOTE, list(deny_baseline.NON_MERGE_RULES))}


def main(argv: list[str]) -> int:
    wanted = files()
    if "--check" in argv:
        stale = [str(p.relative_to(ROOT)) for p, text in wanted.items() if not p.exists() or p.read_text() != text]
        if stale:
            print("stale (run python3 tools/build_harness_deny.py): " + ", ".join(stale), file=sys.stderr)
            return 1
        return 0
    for path, text in wanted.items():
        path.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
