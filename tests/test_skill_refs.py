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



class ToolCoverageTest(unittest.TestCase):
    def test_skills_ask_for_the_search_the_guard_requires(self) -> None:
        import sys
        sys.path.insert(0, str(ROOT / "hooks"))
        from policy import SEARCH_BEFORE_CREATE
        for skill in SKILLS:
            text = skill.read_text()
            for create, searches in SEARCH_BEFORE_CREATE.items():
                if re.search(rf"\b{create}\b", text):
                    with self.subTest(skill=skill.parent.name, create=create):
                        self.assertTrue(
                            any(re.search(rf"\b{s}\b", text) for s in searches),
                            f"{skill.parent.name} names {create} but none of {searches}",
                        )

    def test_inventories_match_the_release_declaration(self) -> None:
        import json
        hooks = json.loads((ROOT / "hooks" / "tools.json").read_text())
        declared = set(hooks["declaredTools"]) - set(hooks["clientOnlyTools"])
        corp = set(hooks["tools"])
        mock = {tool["name"] for tool in json.loads((ROOT / "evals" / "mocks" / "pai" / "_tools.json").read_text())["tools"]}
        index = set(re.findall(r"^\| `([a-z0-9_]+)` \|", (ROOT / "skills" / "pai-console" / "references" / "tools.md").read_text(), re.M))
        self.assertEqual(sorted(declared ^ corp), [], "hooks/tools.json differs from the upstream MCP_TOOL_NAMES")
        self.assertEqual(sorted(corp ^ mock), [], "evals/mocks/pai/_tools.json differs from hooks/tools.json")
        self.assertEqual(sorted(corp ^ index), [], "tools.md differs from hooks/tools.json")
        revision = hooks["generatedFrom"].split()[1]
        self.assertIn(f"`{revision}`", (ROOT / "skills" / "pai-console" / "references" / "tools.md").read_text())
        self.assertIn(revision, (ROOT / "README.md").read_text(), "README does not name the generated release revision")
        self.assertIn(f"**{len(corp)} tools**", (ROOT / "README.md").read_text(), "README states another tool count")

    def test_every_inventory_tool_has_a_workflow(self) -> None:
        import json
        tools = json.loads((ROOT / "hooks" / "tools.json").read_text())["tools"]
        text = "\n".join(skill.read_text() for skill in SKILLS)
        missing = sorted(name for name in tools if not re.search(rf"\b{re.escape(name)}\b", text))
        self.assertEqual(missing, [], "tools without guidance in any SKILL.md")


if __name__ == "__main__":
    unittest.main()
