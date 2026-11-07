"""The orchestration skill documents the session rotation convention."""
from __future__ import annotations

import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "plugins/pai-harness/skills/orchestration/SKILL.md"


class RotationDocsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text()

    def test_states_checkpoint_threshold(self) -> None:
        self.assertIn("about 150k tokens", self.text)

    def test_states_resume_file_convention(self) -> None:
        for needle in ("NOTES-<agent>.md", "uncommitted", "reads the resume file first",
                       "branch and the exact sha", "open pull requests", "waits", "decisions taken"):
            self.assertIn(needle, self.text)

    def test_states_rotate_line(self) -> None:
        self.assertIn("`RELAY-REQUEST rotate <machine>: <agent>`", self.text)
        self.assertIn("--resume", self.text)
        self.assertIn("never relaunch yourself", self.text)

    def test_mentions_quota_line(self) -> None:
        self.assertIn("RELAY-REQUEST SWITCH ACCOUNT <machine>: <who is parked>", self.text)


if __name__ == "__main__":
    unittest.main()
