"""Every harness role is a skill plus an agent: both files, valid frontmatter, an allowed model, a bounded tool list."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "plugins/pai-harness"
sys.path.insert(0, str(HARNESS / "scripts"))
import harness_config  # noqa: E402

# ATE-1174 owns these eight; the distiller and the gate-triager belong to another issue.
ROLES = ("relay", "orchestrator", "lead", "implementer", "root-reviewer", "integrator", "mechanical", "watcher")
MODELS = {"relay": "opus", "orchestrator": "opus", "lead": "sonnet", "implementer": "sonnet",
          "root-reviewer": "opus", "integrator": "sonnet", "mechanical": "haiku", "watcher": "haiku"}
READ_ONLY = {"Read", "Grep", "Glob"}
WRITE_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit", "Agent", "Task"}
REPORT_LINE = re.compile(r"^## Quiet-channel report lines\n(?:.*\n)*?- `", re.M)


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError(f"{path}: no frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            raise AssertionError(f"{path}: bad frontmatter line {line!r}")
        fields[key.strip()] = value.strip().strip('"')
    return fields


def tools(path: Path) -> list[str]:
    return [t.strip() for t in frontmatter(path)["tools"].split(",") if t.strip()]


class RolesTest(unittest.TestCase):
    def test_every_role_has_a_skill_and_an_agent(self) -> None:
        for role in ROLES:
            self.assertTrue((HARNESS / "skills" / role / "SKILL.md").is_file(), role)
            self.assertTrue((HARNESS / "agents" / f"{role}.md").is_file(), role)

    def test_frontmatter_names_the_role_and_describes_it(self) -> None:
        for role in ROLES:
            for path in (HARNESS / "skills" / role / "SKILL.md", HARNESS / "agents" / f"{role}.md"):
                fields = frontmatter(path)
                self.assertEqual(fields["name"], role, path.name)
                self.assertGreater(len(fields["description"]), 20, path.name)

    def test_models_are_allowed_and_match_the_defaults(self) -> None:
        for role in ROLES:
            model = frontmatter(HARNESS / "agents" / f"{role}.md")["model"]
            self.assertIn(model, harness_config.MODEL_CHOICES, role)
            self.assertEqual(model, MODELS[role], role)

    def test_root_reviewer_is_read_only(self) -> None:
        listed = tools(HARNESS / "agents/root-reviewer.md")
        self.assertTrue(listed)
        self.assertEqual(set(listed) - READ_ONLY, set())
        self.assertEqual(set(listed) & WRITE_TOOLS, set())

    def test_only_roles_that_write_may_edit(self) -> None:
        for role in ROLES:
            listed = set(tools(HARNESS / "agents" / f"{role}.md"))
            if role in ("implementer", "lead", "mechanical"):
                continue
            self.assertEqual(listed & {"Edit", "Write", "NotebookEdit"}, set(), role)

    def test_watcher_is_a_script_and_has_only_the_shell(self) -> None:
        self.assertEqual(tools(HARNESS / "agents/watcher.md"), ["Bash"])
        self.assertIn("health.sh", (HARNESS / "skills/watcher/SKILL.md").read_text())

    def test_each_skill_states_duties_inputs_report_lines_and_commands(self) -> None:
        for role in ROLES:
            text = (HARNESS / "skills" / role / "SKILL.md").read_text()
            for heading in ("## Duties", "## Inputs", "## Quiet-channel report lines", "## Scripts and commands"):
                self.assertIn(heading, text, f"{role}: {heading}")
            self.assertRegex(text, REPORT_LINE, role)
            self.assertIn("[models]", text, role)

    def test_skill_commands_exist(self) -> None:
        commands = {p.stem for p in (HARNESS / "commands").glob("*.md") if p.stem != "README"}
        for role in ROLES:
            text = (HARNESS / "skills" / role / "SKILL.md").read_text()
            for used in re.findall(r"`/([a-z-]+)", text):
                self.assertIn(used, commands, f"{role}: /{used}")

    def test_skill_scripts_exist(self) -> None:
        for role in ROLES:
            text = (HARNESS / "skills" / role / "SKILL.md").read_text()
            for script in re.findall(r"scripts/([\w-]+\.sh)", text):
                self.assertTrue((HARNESS / "scripts" / script).is_file(), f"{role}: {script}")


if __name__ == "__main__":
    unittest.main()
