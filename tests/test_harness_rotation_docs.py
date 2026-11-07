"""The orchestration skill documents the session rotation convention."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COPIES = [
    "plugins/pai-harness/skills/orchestration/SKILL.md",
    "skills/orchestration/SKILL.md",
    "plugins/codex-harness/skills/orchestration/SKILL.md",
    "plugins/codex/develop/skills/orchestration/SKILL.md",
    "plugins/codex/staging/skills/orchestration/SKILL.md",
    "plugins/codex/production/skills/orchestration/SKILL.md",
]

# Each statement is anchored on phrases that only the Session rotation section uses.
STATEMENTS = (
    "about 150k tokens",
    "`NOTES-<agent>.md`",
    "Leave it uncommitted",
    "the new session reads the resume file first".capitalize(),
    "the branch and the exact sha",
    "open pull requests",
    "the waits you have armed",
    "and the decisions taken, with the reason for each",
    "`RELAY-REQUEST rotate <machine>: <agent>`, for example",
    "relaunches that agent with `--resume`",
    "You never relaunch yourself",
    "The orchestrator outbox is the append-only file your brief names",
    "`handoff/orchestrator-outbox.md`",
    "not the optional `PAI_WAKE_OUTBOX` file",
    "introduces both request lines as the convention",
    "`RELAY-REQUEST SWITCH ACCOUNT <machine>: <who is parked>`",
    "append the SWITCH ACCOUNT line to the same orchestrator outbox",
)


def section(text: str) -> str:
    match = re.search(r"^## Session rotation\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if match is None:
        raise AssertionError("Session rotation section not found")
    return match.group(1)


class RotationDocsTest(unittest.TestCase):
    def test_every_copy_states_every_rule_in_the_section(self) -> None:
        for rel in COPIES:
            body = section((ROOT / rel).read_text())
            for needle in STATEMENTS:
                with self.subTest(copy=rel, needle=needle):
                    self.assertIn(needle, body)

    def test_section_extraction_is_scoped(self) -> None:
        body = section((ROOT / COPIES[0]).read_text())
        self.assertNotIn("## Closing", body)
        self.assertNotIn("orchestration-wake plugin", body.split("PAI_WAKE_OUTBOX")[-1])

    def test_removing_a_statement_fails(self) -> None:
        body = section((ROOT / COPIES[0]).read_text())
        for needle in STATEMENTS:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, body.replace(needle, ""))


if __name__ == "__main__":
    unittest.main()
