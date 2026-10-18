"""Each SKILL.md cites its files relative to its own directory (ATE-242).

A skill can load from a base path where ${CLAUDE_PLUGIN_ROOT} does not
resolve, so a citation is `references/…` or `examples/…` (this skill),
`../<skill>/…` (another skill) or `../../<path>` (the plugin root), and the
file it names exists.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))

# A backticked path into the skill's own files or out of the skill.
RELATIVE = re.compile(r"`((?:\.\./)+[^`\s]+|(?:references|examples)/[^`\s]*)`")
# The forms that depend on where the plugin root is.
ROOTED = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}|`skills/[a-z0-9-]+/")


class SkillReferencesTest(unittest.TestCase):
    def test_skills_found(self) -> None:
        self.assertGreater(len(SKILLS), 10)

    def test_no_plugin_root_paths(self) -> None:
        for skill in SKILLS:
            for number, line in enumerate(skill.read_text().splitlines(), 1):
                with self.subTest(skill=skill.parent.name, line=number):
                    self.assertIsNone(
                        ROOTED.search(line),
                        f"{skill.relative_to(ROOT)}:{number} references the plugin root; use a skill-relative path",
                    )

    def test_relative_references_exist(self) -> None:
        for skill in SKILLS:
            for number, line in enumerate(skill.read_text().splitlines(), 1):
                for match in RELATIVE.finditer(line):
                    cited = match.group(1).split("#")[0]
                    if "…" in cited or "<" in cited:
                        continue  # A pattern (`references/…`, `../<skill>/…`), not a file.
                    target = (skill.parent / cited).resolve()
                    with self.subTest(skill=skill.parent.name, cited=cited):
                        self.assertTrue(
                            target.is_relative_to(ROOT),
                            f"{skill.relative_to(ROOT)}:{number} escapes the plugin: {cited}",
                        )
                        self.assertTrue(
                            target.exists(),
                            f"{skill.relative_to(ROOT)}:{number} references missing file {cited}",
                        )


if __name__ == "__main__":
    unittest.main()
