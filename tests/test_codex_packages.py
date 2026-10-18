"""Portable package contracts and deterministic generation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_codex", ROOT / "tools/build_codex.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class CodexPackagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = build.expected_files(ROOT)

    def package_json(self, env, path):
        return json.loads(self.expected[Path("plugins/codex") / env / path])

    def test_environment_identity_mcp_and_oauth(self):
        for env, url in build.ENVIRONMENTS.items():
            with self.subTest(environment=env):
                manifest = self.package_json(env, "plugin.json")
                self.assertEqual(manifest["name"], f"pai-console-{env}")
                self.assertEqual(manifest["version"], "0.0.9")
                self.assertIn("agent-plugins.org", manifest["$schema"])
                self.assertEqual(manifest["extensions"]["com.openai"]["hooks"], "./hooks/codex_hooks.json")
                self.assertEqual(manifest["extensions"]["com.openai"]["onboardingSkill"], "./skills/setup/SKILL.md")
                self.assertEqual(self.package_json(env, "environment.json"), {
                    "environment": env, "url": url, "plugin_name": f"pai-console-{env}", "server_name": f"pai_console_{env}"})
                servers = self.package_json(env, "mcp.json")["mcpServers"]
                self.assertEqual(set(servers), {f"pai_console_{env}"})
                server = servers[f"pai_console_{env}"]
                self.assertEqual(server["type"], "streamable-http")
                self.assertEqual(server["url"], url)
                self.assertEqual(server["extensions"]["com.openai"]["auth"], {
                    "type": "oauth", "client": {"mode": "dcr"}, "baseScopes": ["pai:manage"]})
                self.assertNotIn("userConfig", manifest)

    def test_marketplace_local_paths_and_policy(self):
        catalog = json.loads(self.expected[Path(".agents/plugins/marketplace.json")])
        self.assertEqual(catalog["name"], build.MARKETPLACE)
        for env, entry in zip(build.ENVIRONMENTS, catalog["plugins"]):
            self.assertEqual(entry["source"], {"source": "local", "path": f"./plugins/codex/{env}"})
            self.assertEqual(entry["policy"], {"installation": "AVAILABLE", "authentication": "ON_INSTALL"})
            self.assertEqual(entry["category"], "Productivity")

    def test_shared_sources_runtime_and_overrides(self):
        for env in build.ENVIRONMENTS:
            base = Path("plugins/codex") / env
            for source in (ROOT / "skills").rglob("*"):
                if source.is_file() and source.relative_to(ROOT / "skills").parts[0] not in build.codex_skills():
                    self.assertEqual(self.expected[base / source.relative_to(ROOT)], source.read_bytes())
            for runtime in build.RUNTIME:
                self.assertEqual(self.expected[base / "hooks" / runtime], (ROOT / "hooks" / runtime).read_bytes())
            self.assertEqual(self.expected[base / "tools/codex_plugin.py"], (ROOT / "tools/codex_plugin.py").read_bytes())
            self.assertNotIn(base / "hooks/hooks.json", self.expected)
            self.assertNotIn(base / "agents/pai-explorer.md", self.expected)
            self.assertIn(b"8 preview attempts", self.expected[base / "skills/theme-designer/SKILL.md"])
            self.assertNotIn(b"claude plugin", self.expected[base / "skills/pai-env/SKILL.md"])
            self.assertIn(b"../../tools/codex_plugin.py", self.expected[base / "skills/pai-env/SKILL.md"])

    def test_explicit_environment_invocation_and_discoverable_setup_metadata(self):
        for env in build.ENVIRONMENTS:
            base = Path("plugins/codex") / env / "skills"
            self.assertEqual(self.expected[base / "pai-env/agents/openai.yaml"].decode(),
                             "policy:\n  allow_implicit_invocation: false\n")
            self.assertEqual(self.expected[base / "setup/agents/openai.yaml"].decode(),
                             "policy:\n  allow_implicit_invocation: true\n")
            for name in ("pai-env", "setup"):
                body = self.expected[base / name / "SKILL.md"].decode()
                self.assertIn('"$pai_skill_dir/../../tools/codex_plugin.py"', body)
                self.assertNotIn("python3 ../../tools/codex_plugin.py", body)

    def test_package_skill_references_are_self_contained(self):
        relative = re.compile(r"`((?:\.\./)+[^`\s]+|(?:references|examples)/[^`\s]*)`")
        for path, content in self.expected.items():
            if path.name != "SKILL.md":
                continue
            base = Path(*path.parts[:3])
            for match in relative.finditer(content.decode()):
                reference = match[1].split("#")[0]
                if any(token in reference for token in ("<", "…", "*")):
                    continue
                target = (ROOT / path.parent / reference).resolve().relative_to(ROOT)
                with self.subTest(skill=path, reference=reference):
                    self.assertTrue(target.is_relative_to(base))
                    self.assertTrue(target in self.expected or any(p.is_relative_to(target) for p in self.expected),
                                    f"Missing packaged reference: {target}")

    def test_reproducibility_check_and_stale_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "skills", root / "skills")
            shutil.copytree(ROOT / "hooks", root / "hooks")
            (root / "tools").mkdir()
            for filename in ("codex_plugin.py", "validate-examples.ts"):
                shutil.copy2(ROOT / "tools" / filename, root / "tools" / filename)
            (root / "evals/mocks/pai").mkdir(parents=True)
            shutil.copy2(ROOT / "evals/mocks/pai/_tools.json", root / "evals/mocks/pai/_tools.json")
            self.assertTrue(build.build(root, check=True))
            build.build(root)
            self.assertEqual(build.build(root, check=True), [])
            target = root / "plugins/codex/staging/environment.json"
            original = target.read_bytes()
            target.write_bytes(b"{}")
            self.assertIn("plugins/codex/staging/environment.json", build.build(root, check=True))
            self.assertEqual(target.read_bytes(), b"{}")
            stale = root / "plugins/codex/staging/stale.txt"
            stale.write_text("obsolete")
            build.build(root)
            self.assertEqual(target.read_bytes(), original)
            self.assertFalse(stale.exists())
            self.assertEqual(build.build(root, check=True), [])

    def test_claude_contract_is_preserved(self):
        manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "pai-console")
        self.assertEqual(manifest["version"], "0.0.9")
        self.assertEqual(manifest["mcpServers"]["pai"]["url"], "${user_config.mcp_url}")
        self.assertEqual(len(manifest["userConfig"]["mcp_url"]["options"]), 4)
        self.assertTrue((ROOT / "agents/pai-explorer.md").is_file())
        self.assertTrue((ROOT / "agents/theme-designer.md").is_file())


if __name__ == "__main__":
    unittest.main()
