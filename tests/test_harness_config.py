"""pai-harness plugin: manifest, marketplace entry, copied skills, .pai-harness.toml schema, validator and loader."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins/pai-harness"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(PLUGIN / "scripts"))
import build_codex  # noqa: E402
import harness_config as hc  # noqa: E402

VALID = '[project]\npai_org = "acme"\npai_project = "acme-app"\nlinear_team = "ACME"\n'


HOTFIX = ('[gates.hotfix]\nactive_when = "make typecheck-all"\napplies_to = "release-red"\npre_merge = ["make typecheck-all"]\n'
          'post_merge = "make gate-full"\nrevert_on_failure = true\n')


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PLUGIN / "scripts" / script), *args], capture_output=True, text=True)


class PluginLayoutTest(unittest.TestCase):
    def test_manifest_matches_the_contract(self) -> None:
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
        console = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual((manifest["name"], manifest["version"], manifest["license"]), ("pai-harness", "0.1.0", "UNLICENSED"))
        self.assertEqual(manifest["author"], console["author"])

    def test_marketplace_has_a_second_entry_and_leaves_pai_console_alone(self) -> None:
        plugins = {p["name"]: p for p in json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"]}
        self.assertEqual(sorted(plugins), ["pai-console", "pai-harness"])
        self.assertEqual(plugins["pai-harness"]["source"], "./plugins/pai-harness")
        self.assertEqual(plugins["pai-console"]["source"], "./")

    def test_empty_directories_each_carry_a_readme(self) -> None:
        for name in ("skills", "agents", "commands", "hooks", "scripts", "herdr-plugins"):
            self.assertTrue((PLUGIN / name / "README.md").is_file(), name)

    def test_orchestration_skill_is_copied_and_herdr_is_vendored(self) -> None:
        copied = (PLUGIN / "skills/orchestration/SKILL.md").read_text()
        original = (ROOT / "skills/orchestration/SKILL.md").read_text()
        # Only the install source is generic here; the repository name stays out of the plugin.
        self.assertEqual(copied, original.replace("pailat/pai-console-plugin", "<owner>/<marketplace-repo>"))
        self.assertEqual((PLUGIN / "skills/herdr/SKILL.md").read_bytes(), (ROOT / "skills/herdr/SKILL.md").read_bytes())
        build_codex.herdr_vendor(ROOT)

    def test_codex_package_is_generated_and_reproducible(self) -> None:
        self.assertEqual(build_codex.build(ROOT, check=True), [])
        package = ROOT / build_codex.HARNESS_CODEX
        self.assertEqual(json.loads((package / "plugin.json").read_text())["version"], "0.1.0")
        self.assertTrue((package / "scripts/validate_config.py").is_file())
        self.assertTrue((package / "skills/orchestration/agents/openai.yaml").is_file())


class ConfigTest(unittest.TestCase):
    def test_a_repo_with_only_the_example_file_loads_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            shutil.copy(PLUGIN / "examples/acme/.pai-harness.toml", repo / ".pai-harness.toml")
            (repo / "sub/dir").mkdir(parents=True)
            self.assertEqual(run("validate_config.py", str(repo)).returncode, 0)
            self.assertEqual(run("validate_config.py", str(repo / "sub/dir")).returncode, 0)  # finds the file upward
            loaded = run("load_config.py", str(repo))
            self.assertEqual(loaded.returncode, 0, loaded.stderr)
            config = json.loads(loaded.stdout)
        self.assertEqual(config["project"]["linear_team"], "ACME")
        self.assertEqual(config["gates"]["lint"], ["make lint", "make typecheck"])
        self.assertEqual(config["limits"]["max_agents"], 6)
        self.assertEqual(config["limits"]["max_open_prs"], 5)  # default

    def test_hotfix_is_a_typed_table_and_other_gates_stay_commands(self) -> None:
        config = hc.validate(__import__("tomllib").loads(VALID + '[gates]\nunit = "make test"\n' + HOTFIX))
        self.assertEqual(config["gates"]["unit"], ["make test"])
        self.assertEqual(config["gates"]["hotfix"], {"active_when": "make typecheck-all", "applies_to": "release-red", "pre_merge": ["make typecheck-all"],
                                                     "post_merge": "make gate-full", "revert_on_failure": True})
        default = hc.validate(__import__("tomllib").loads(VALID + HOTFIX.replace("revert_on_failure = true\n", "")))
        self.assertTrue(default["gates"]["hotfix"]["revert_on_failure"])

    def test_the_acme_example_shows_the_hotfix_profile(self) -> None:
        config = hc.load_file(PLUGIN / "examples/acme/.pai-harness.toml")
        self.assertEqual(sorted(config["gates"]), ["hotfix", "lint", "unit"])
        self.assertEqual(config["gates"]["hotfix"]["post_merge"], "make gate-full")

    def test_minimal_file_gets_defaults(self) -> None:
        config = hc.validate(__import__("tomllib").loads(VALID))
        self.assertEqual(config["models"], hc.DEFAULT_MODELS)
        self.assertEqual(config["project"]["issue_prefix"], "ACME")
        self.assertEqual(config["gates"], {})

    def test_bad_files_fail_naming_the_key(self) -> None:
        cases = {
            "project": ('[limits]\nmax_agents = 2\n', "project: required section is missing"),
            "project.linear_team": ('[project]\npai_org = "a"\npai_project = "b"\n', "project.linear_team"),
            "project.colour": (VALID + 'colour = "red"\n', "project.colour: unknown key"),
            "limits.max_agents": (VALID + '[limits]\nmax_agents = "six"\n', "limits.max_agents: expected integer"),
            "limits.max_open_prs": (VALID + '[limits]\nmax_open_prs = 0\n', "limits.max_open_prs: must be at least 1"),
            "models.implementer": (VALID + '[models]\nimplementer = "gpt"\n', "models.implementer: unknown model"),
            "models.pilot": (VALID + '[models]\npilot = "opus"\n', "models.pilot: unknown key"),
            "zones.web.globs": (VALID + '[zones.web]\nowners = ["x"]\n', "zones.web.globs: required key is missing"),
            "zones.web.globs[0]": (VALID + '[zones.web]\nglobs = [3]\n', "zones.web.globs[0]: expected string"),
            "queues.q.machine": (VALID + '[queues.q]\nmachine = "nowhere"\n', "queues.q.machine: unknown machine"),
            "gates.Unit": (VALID + '[gates]\nUnit = "make test"\n', "gates.Unit: name must be"),
            "gates.hotfix": (VALID + '[gates]\nhotfix = "make test"\n', "gates.hotfix: expected table"),
            "gates.hotfix.post_merge": (VALID + HOTFIX.replace('post_merge = "make gate-full"\n', ''), "gates.hotfix.post_merge: required key is missing"),
            "gates.hotfix.pre_merge": (VALID + HOTFIX.replace('["make typecheck-all"]', '[]'), "gates.hotfix.pre_merge: command list must not be empty"),
            "gates.hotfix.applies_to": (VALID + HOTFIX.replace('"release-red"', '"("'), "gates.hotfix.applies_to: invalid regular expression"),
            "gates.hotfix.revert_on_failure": (VALID + HOTFIX.replace("true", '"yes"'), "gates.hotfix.revert_on_failure: expected boolean"),
            "gates.hotfix.colour": (VALID + HOTFIX + 'colour = "red"\n', "gates.hotfix.colour: unknown key"),
            "bogus": ('bogus = 1\n' + VALID, "bogus: unknown section"),
            "schema_version": ('schema_version = 2\n' + VALID, "schema_version: unsupported"),
        }
        for key, (text, message) in cases.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / ".pai-harness.toml"
                path.write_text(text)
                result = run("validate_config.py", str(path))
                self.assertEqual(result.returncode, 1, text)
                self.assertIn(message, result.stderr)

    def test_invalid_toml_and_missing_file_fail_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".pai-harness.toml"
            path.write_text("[project\n")
            self.assertIn("invalid TOML", run("validate_config.py", str(path)).stderr)
            path.unlink()
            self.assertIn("no .pai-harness.toml found", run("load_config.py", tmp).stderr)

    def test_json_schema_agrees_with_the_validator(self) -> None:
        schema = json.loads((PLUGIN / "schema/pai-harness.schema.json").read_text())
        self.assertEqual(sorted(schema["properties"]), sorted(["schema_version", *hc.DEFAULTS.keys() - {"schema_version"}]))
        self.assertEqual(schema["required"], ["project"])
        self.assertEqual(sorted(schema["properties"]["models"]["properties"]), sorted(hc.ROLES))
        self.assertEqual(schema["properties"]["models"]["default"], hc.DEFAULT_MODELS)
        self.assertEqual(sorted(schema["properties"]["limits"]["properties"]), sorted(hc.DEFAULTS["limits"]))
        self.assertEqual(sorted(schema["properties"]["rules"]["properties"]), sorted(hc.DEFAULTS["rules"]))
        hotfix = schema["properties"]["gates"]["properties"]["hotfix"]
        self.assertEqual(sorted(hotfix["properties"]), ["active_when", "applies_to", "post_merge", "pre_merge", "revert_on_failure"])
        self.assertEqual(hotfix["required"], ["active_when", "applies_to", "pre_merge", "post_merge"])
        self.assertEqual(schema["properties"]["models"]["properties"]["lead"]["enum"], [m for m in hc.MODEL_CHOICES if m != "none"])


if __name__ == "__main__":
    unittest.main()
