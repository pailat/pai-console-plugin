"""ATE-1223 owner policy: bypassPermissions by default, deny rules and hooks as the safety, no doc that forbids bypass."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import PLUGIN_ROOT, ROOT, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import harness_config  # noqa: E402

FORBIDS = re.compile(r"(never|do not|don't|must not)\s+(pass|use|add)[^.\n]{0,40}permission[- ]bypass|permission-bypass flag|"
                     r"no[- ]permission[- ]bypass", re.I)
MINIMAL = '[project]\npai_org = "acme"\npai_project = "acme-web"\nlinear_team = "ACME"\n'


class NoDocForbidsBypassTest(unittest.TestCase):
    def test_no_agent_command_skill_doc_or_generated_package_forbids_bypass(self) -> None:
        roots = [PLUGIN_ROOT / d for d in ("agents", "commands", "skills", "docs", "scripts", "examples")]
        roots += [ROOT / "plugins/codex-harness", ROOT / "README.md"]
        offenders = []
        for base in roots:
            for path in ([base] if base.is_file() else sorted(base.rglob("*"))):
                if path.is_file() and path.suffix in {".md", ".py", ".toml", ".json", ".sh"}:
                    if FORBIDS.search(path.read_text(errors="ignore")):
                        offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_every_agent_states_the_policy(self) -> None:
        agents = sorted((PLUGIN_ROOT / "agents").glob("*.md"))
        for path in agents:
            if path.name == "README.md":
                continue
            text = path.read_text()
            self.assertIn("bypassPermissions", text, path.name)
            self.assertIn("BLOCKER", text, path.name)


class LauncherPolicyTest(HarnessCase):
    def argv(self) -> list[str]:
        return json.loads((self.tmp / "claude.json").read_text())["argv"]

    def test_default_passes_bypass_permissions(self) -> None:
        self.launch("ACME-7", "success", 0)
        argv = self.argv()
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "bypassPermissions")

    def test_project_opt_out_drops_the_flag(self) -> None:
        config = self.tmp / "optout.toml"
        config.write_text(MINIMAL + "\n[run]\nbypass_permissions = false\n")
        self.env["PAI_HARNESS_CONFIG"] = str(config)
        self.launch("ACME-7", "success", 0)
        self.assertNotIn("--permission-mode", self.argv())
        self.assertNotIn("bypassPermissions", self.argv())


class ConfigKeyTest(unittest.TestCase):
    def test_default_true_and_opt_out(self) -> None:
        self.assertIs(harness_config.validate({"project": {"pai_org": "a", "pai_project": "b", "linear_team": "ACME"}})["run"]["bypass_permissions"], True)
        data = {"project": {"pai_org": "a", "pai_project": "b", "linear_team": "ACME"}, "run": {"bypass_permissions": False}}
        self.assertIs(harness_config.validate(data)["run"]["bypass_permissions"], False)

    def test_rejects_a_non_boolean_and_unknown_keys(self) -> None:
        base = {"project": {"pai_org": "a", "pai_project": "b", "linear_team": "ACME"}}
        for run in ({"bypass_permissions": "no"}, {"mode": "x"}):
            with self.assertRaises(harness_config.ConfigError):
                harness_config.validate({**base, "run": run})

    def test_schema_documents_the_key(self) -> None:
        schema = json.loads((PLUGIN_ROOT / "schema/pai-harness.schema.json").read_text())
        self.assertEqual(sorted(schema["properties"]["run"]["properties"]), sorted(harness_config.DEFAULTS["run"]))


class DenyExampleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.deny = json.loads((PLUGIN_ROOT / "examples/settings.deny.json").read_text())["permissions"]["deny"]

    def test_parses_with_claude_code_rule_syntax(self) -> None:
        self.assertTrue(self.deny and len(set(self.deny)) == len(self.deny))
        for rule in self.deny:
            self.assertRegex(rule, r"^(Bash|Read|Edit|Write)\(.+\)$")

    def test_covers_the_owner_list(self) -> None:
        text = "\n".join(self.deny)
        for needle in ("git push --force", "git push --delete", "git push --mirror", "git push * +*", "--no-verify", "git push origin main",
                       "git reset --hard", "git clean -f", "git branch -D", "git checkout .", "git restore .", "git commit --no-verify",
                       "rm -rf /", "rm -rf ~", "rm -rf $HOME", "rm -rf ..", "rm -rf .git", "sudo", "ssh", "scp", "Read(./.env)", "gh repo delete"):
            self.assertIn(needle, text, needle)

    def test_is_generic(self) -> None:
        raw = (PLUGIN_ROOT / "examples/settings.deny.json").read_text()
        self.assertNotRegex(raw, r"/home/|/Users/|pailat|pai-console")


if __name__ == "__main__":
    unittest.main()
