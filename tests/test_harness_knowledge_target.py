"""ATE-1202: the [knowledge] target in the config, its stream override, the launcher exports and the fail-closed BLOCKER."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, PLUGIN_ROOT, HarnessCase  # noqa: E402

sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
import harness_config as hc  # noqa: E402

BASE = '[project]\npai_org = "acme"\npai_project = "acme-app"\nlinear_team = "ACME"\n'
TARGET = BASE + '[knowledge]\norganization = "acme"\nproject = "acme-app"\n'
KNOWLEDGE = FIXTURES / "knowledge.pai-harness.toml"
ACME = FIXTURES / "acme.pai-harness.toml"
DELTA = FIXTURES.parent / "harness-distiller"


def load(text: str) -> dict:
    import tomllib
    return hc.validate(tomllib.loads(text))


class KnowledgeConfigTest(unittest.TestCase):
    def test_a_config_without_a_target_loads_and_resolves_nothing(self) -> None:
        config = load(BASE)
        self.assertEqual(config["knowledge"], {})
        self.assertIsNone(hc.resolve_knowledge(config))
        self.assertIsNone(hc.resolve_knowledge(config, "main"))

    def test_a_config_with_a_project_target_resolves_it(self) -> None:
        config = load(TARGET)
        self.assertEqual(hc.resolve_knowledge(config), {"organization": "acme", "project": "acme-app", "stream": None})

    def test_a_product_target_is_accepted(self) -> None:
        config = load(BASE + '[knowledge]\norganization = "acme"\nproduct = "acme-storefront"\n')
        self.assertEqual(hc.resolve_knowledge(config)["product"], "acme-storefront")

    def test_a_stream_override_wins_and_inherits_the_organization(self) -> None:
        config = load(TARGET + '[knowledge.streams.main]\nproduct = "acme-storefront"\n[knowledge.streams.other]\norganization = "acme-labs"\nproject = "labs"\n')
        self.assertEqual(hc.resolve_knowledge(config, "main"), {"organization": "acme", "product": "acme-storefront", "stream": "main"})
        self.assertEqual(hc.resolve_knowledge(config, "other"), {"organization": "acme-labs", "project": "labs", "stream": "other"})

    def test_a_stream_without_an_override_uses_the_default(self) -> None:
        config = load(TARGET + '[knowledge.streams.main]\nproduct = "acme-storefront"\n')
        self.assertEqual(hc.resolve_knowledge(config, "unlisted"), {"organization": "acme", "project": "acme-app", "stream": None})

    def test_bad_targets_are_rejected_naming_the_key(self) -> None:
        cases = {
            "neither": ('[knowledge]\norganization = "acme"\n', "knowledge: name exactly one of project or product (neither given)"),
            "both": ('[knowledge]\norganization = "acme"\nproject = "p"\nproduct = "q"\n', "(both given)"),
            "no organization": ('[knowledge]\nproject = "p"\n', "knowledge.organization: required"),
            "unknown key": ('[knowledge]\norganization = "acme"\nproject = "p"\nrepo = "x"\n', "knowledge.repo: unknown key"),
            "bad type": ('[knowledge]\norganization = "acme"\nproject = 7\n', "knowledge.project: expected string"),
            "empty": ('[knowledge]\norganization = "acme"\nproject = " "\n', "knowledge.project: must not be empty"),
            "stream neither": ('[knowledge]\norganization = "acme"\nproject = "p"\n[knowledge.streams.main]\norganization = "acme"\n', "knowledge.streams.main: name exactly one"),
            "stream both": ('[knowledge]\norganization = "acme"\nproject = "p"\n[knowledge.streams.main]\nproject = "p"\nproduct = "q"\n', "knowledge.streams.main"),
            "stream unknown key": ('[knowledge]\norganization = "acme"\nproject = "p"\n[knowledge.streams.main]\nproject = "p"\nx = "y"\n', "knowledge.streams.main.x: unknown key"),
            "stream bad name": ('[knowledge]\norganization = "acme"\nproject = "p"\n[knowledge.streams.Main]\nproject = "p"\n', "knowledge.streams.Main: name must be"),
            "streams without a default": ('[knowledge.streams.main]\nproject = "p"\n', "knowledge"),
        }
        for label, (text, message) in cases.items():
            with self.subTest(label), self.assertRaisesRegex(hc.ConfigError, message.replace("(", r"\(").replace(")", r"\)")):
                load(BASE + text)

    def test_the_validator_script_checks_it(self) -> None:
        script = str(PLUGIN_ROOT / "scripts/validate_config.py")
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = Path(tmp) / "good.toml", Path(tmp) / "bad.toml"
            good.write_text(TARGET)
            bad.write_text(BASE + '[knowledge]\norganization = "acme"\n')
            self.assertEqual(subprocess.run([sys.executable, script, str(good)], capture_output=True, text=True).returncode, 0)
            refused = subprocess.run([sys.executable, script, str(bad)], capture_output=True, text=True)
            self.assertEqual(refused.returncode, 1)
            self.assertIn("exactly one of project or product", refused.stderr)

    def test_the_acme_example_names_a_target(self) -> None:
        config = hc.load_file(PLUGIN_ROOT / "examples/acme/.pai-harness.toml")
        self.assertEqual(hc.resolve_knowledge(config)["project"], "acme-app")
        self.assertEqual(hc.resolve_knowledge(config, "main")["product"], "acme-storefront")

    def test_the_json_schema_describes_it(self) -> None:
        schema = json.loads((PLUGIN_ROOT / "schema/pai-harness.schema.json").read_text())["properties"]["knowledge"]
        self.assertEqual(schema["required"], ["organization"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(sorted(schema["properties"]), ["organization", "product", "project", "streams"])
        stream = schema["properties"]["streams"]["additionalProperties"]
        self.assertEqual(sorted(stream["properties"]), ["organization", "product", "project"])
        self.assertEqual(len(schema["oneOf"]), 2)
        self.assertEqual(len(stream["oneOf"]), 2)

    def test_the_docs_cover_the_target(self) -> None:
        text = (PLUGIN_ROOT / "docs/knowledge-target.md").read_text()
        for needle in ("[knowledge.streams.", "PAI_HARNESS_KNOWLEDGE_ORG", "no knowledge target resolved for ROLE/STREAM", "page_search"):
            self.assertIn(needle, text)


class LauncherKnowledgeTest(HarnessCase):
    def setUp(self) -> None:
        super().setUp()
        self.env["PAI_HARNESS_CONFIG"] = str(KNOWLEDGE)
        for name in [k for k in self.env if k.startswith("PAI_HARNESS_KNOWLEDGE") or k == "PAI_HARNESS_STREAM"]:
            self.env.pop(name)

    def probe(self, *extra: str, **env: str) -> tuple[subprocess.CompletedProcess, dict, str]:
        probe = self.tmp / "probe_claude.py"
        probe.write_text("import json, os, sys\nprompt = sys.stdin.read()\n"
                         "json.dump({'env': {k: v for k, v in os.environ.items() if k.startswith('PAI_HARNESS_')}, 'prompt': prompt}, open(os.environ['PROBE_LOG'], 'w'))\n"
                         "print(open(os.environ['FAKE_CLAUDE_FIXTURE']).read(), end='')\n")
        wrapper = self.tmp / "claude"
        wrapper.write_text(f"#!/bin/sh\nexec {sys.executable} {probe} \"$@\"\n")
        wrapper.chmod(0o755)
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), *extra, PAI_HARNESS_CLAUDE=str(wrapper),
                               FAKE_CLAUDE_FIXTURE=str(self.fixture("success")), PROBE_LOG=str(self.tmp / "probe.json"), **env)
        seen = json.loads((self.tmp / "probe.json").read_text()) if (self.tmp / "probe.json").exists() else {}
        return done, seen.get("env", {}), seen.get("prompt", "")

    def test_the_default_target_is_exported_with_a_brief_header(self) -> None:
        done, env, prompt = self.probe()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual((env["PAI_HARNESS_KNOWLEDGE_ORG"], env["PAI_HARNESS_KNOWLEDGE_PROJECT"]), ("acme", "acme-app"))
        self.assertNotIn("PAI_HARNESS_KNOWLEDGE_PRODUCT", env)
        self.assertNotIn("PAI_HARNESS_STREAM", env)
        self.assertEqual(prompt.splitlines()[0], "Knowledge target: organization=acme project=acme-app")
        self.assertIn("Implement ACME-7", prompt)
        self.assertEqual(self.prompt.read_text(), "Implement ACME-7 for the Acme app.\n")  # the caller's brief file is untouched

    def test_the_queue_name_picks_a_stream_override(self) -> None:
        _, env, prompt = self.probe("--queue", "side")
        self.assertEqual((env["PAI_HARNESS_KNOWLEDGE_PRODUCT"], env["PAI_HARNESS_STREAM"]), ("acme-storefront", "side"))
        self.assertNotIn("PAI_HARNESS_KNOWLEDGE_PROJECT", env)
        self.assertEqual(prompt.splitlines()[0], "Knowledge target: organization=acme product=acme-storefront stream=side")

    def test_the_stream_option_wins_over_the_queue(self) -> None:
        _, env, _ = self.probe("--queue", "main", "--stream", "side")
        self.assertEqual(env["PAI_HARNESS_KNOWLEDGE_PRODUCT"], "acme-storefront")
        _, env, _ = self.probe("--queue", "side")
        self.assertEqual(env["PAI_HARNESS_KNOWLEDGE_PRODUCT"], "acme-storefront")

    def test_a_queue_without_an_override_uses_the_default(self) -> None:
        _, env, _ = self.probe("--queue", "main")
        self.assertEqual(env["PAI_HARNESS_KNOWLEDGE_PROJECT"], "acme-app")
        self.assertEqual(env["PAI_HARNESS_STREAM"], "main")

    def test_an_unknown_stream_option_is_a_usage_error(self) -> None:
        done, env, _ = self.probe("--stream", "nope")
        self.assertEqual(done.returncode, 2)
        self.assertIn("nope", done.stderr)
        self.assertEqual(env, {})

    def test_a_stale_target_in_the_environment_does_not_leak(self) -> None:
        self.env["PAI_HARNESS_CONFIG"] = str(ACME)
        done, env, prompt = self.probe(PAI_HARNESS_KNOWLEDGE_ORG="stale", PAI_HARNESS_KNOWLEDGE_PROJECT="stale", PAI_HARNESS_STREAM="stale")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse([k for k in env if k.startswith("PAI_HARNESS_KNOWLEDGE")] + [k for k in env if k == "PAI_HARNESS_STREAM"])
        self.assertEqual(prompt, "Implement ACME-7 for the Acme app.\n")  # no header for a role that has no target to name

    def test_no_target_tells_a_distiller_in_its_brief(self) -> None:
        self.env["PAI_HARNESS_CONFIG"] = str(ACME)
        _, env, prompt = self.probe("--role", "distiller")
        self.assertNotIn("PAI_HARNESS_KNOWLEDGE_ORG", env)
        self.assertEqual(prompt.splitlines()[0], "Knowledge target: none resolved for distiller/default")

    def test_the_dry_run_shows_the_target(self) -> None:
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), "--queue", "side", "--dry-run")
        shown = json.loads(done.stdout)["hook_env"]
        self.assertEqual((shown["PAI_HARNESS_KNOWLEDGE_ORG"], shown["PAI_HARNESS_KNOWLEDGE_PRODUCT"]), ("acme", "acme-storefront"))


class FailClosedTest(unittest.TestCase):
    SCRIPT = str(PLUGIN_ROOT / "scripts/delta_marker.py")

    def run_marker(self, config: Path, tmp: str, *args: str, **env: str) -> subprocess.CompletedProcess:
        clean = {"PAI_HARNESS_STATE_DIR": tmp, "PATH": "/usr/bin:/bin", **env}
        return subprocess.run([sys.executable, self.SCRIPT, "--config", str(config), *args], capture_output=True, text=True, env=clean)

    def test_write_without_a_target_is_a_named_blocker_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(ACME, tmp, "write", "acme-42", "kn-acme-0031", PAI_HARNESS_ROLE="distiller")
            self.assertEqual(done.returncode, 1)
            self.assertIn("BLOCKER acme-42: no knowledge target resolved for distiller/default", done.stdout)
            self.assertFalse((Path(tmp) / "deltas").exists())
            self.assertIn("no knowledge target resolved", (Path(tmp) / "journal.jsonl").read_text())

    def test_plan_without_a_target_is_the_same_blocker_and_names_the_stream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(ACME, tmp, "plan", str(DELTA / "candidates.json"), str(DELTA / "existing-nodes.json"), PAI_HARNESS_STREAM="side")
            self.assertEqual(done.returncode, 1)
            self.assertIn("no knowledge target resolved for distiller/side", done.stdout)
            self.assertNotIn('"create"', done.stdout)

    def test_an_unreadable_config_resolves_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(Path(tmp) / "missing.toml", tmp, "write", "acme-42", "kn-1")
            self.assertNotEqual(done.returncode, 0)
            self.assertFalse((Path(tmp) / "deltas").exists())

    def test_the_launcher_exports_open_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(ACME, tmp, "write", "acme-42", "kn-acme-0031", PAI_HARNESS_KNOWLEDGE_ORG="acme", PAI_HARNESS_KNOWLEDGE_PRODUCT="acme-storefront")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue((Path(tmp) / "deltas/acme-42.json").is_file())

    def test_both_scopes_exported_is_not_a_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(ACME, tmp, "write", "acme-42", "kn-1", PAI_HARNESS_KNOWLEDGE_ORG="acme", PAI_HARNESS_KNOWLEDGE_PROJECT="a", PAI_HARNESS_KNOWLEDGE_PRODUCT="b")
            self.assertEqual(done.returncode, 1)

    def test_the_config_resolves_the_stream_when_nothing_is_exported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(KNOWLEDGE, tmp, "write", "acme-42", "kn-acme-0031", PAI_HARNESS_STREAM="side")
            self.assertEqual(done.returncode, 0, done.stderr)

    def test_the_skill_names_the_same_blocker(self) -> None:
        text = (PLUGIN_ROOT / "skills/distiller/SKILL.md").read_text()
        self.assertIn("## Knowledge target", text)
        self.assertIn("BLOCKER no knowledge target resolved for distiller/<stream>", text)
        self.assertIn("PAI_HARNESS_KNOWLEDGE_ORG", text)


if __name__ == "__main__":
    unittest.main()
