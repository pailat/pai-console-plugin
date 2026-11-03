"""The herdr dependency, its Codex vendoring, the wake plugin and the no-symlink rule (ATE-709)."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import shutil
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_codex  # noqa: E402

SHA = re.compile(r"^[0-9a-f]{40}$")
# One leak guard for everything this repository publishes about orchestration (wake plugin and skill): machine and network
# identifiers, real pane ids, owner contact, and the internal roster, decision ids, workflow names and process vocabulary.
LEAK = re.compile(
    r"/home/|/Users/|~/worktrees|omarchy|macbook|\bw[A-Z]{2}:p[0-9A-Z]+|100\.\d+\.\d+\.\d+|ts\.net|@pai\.lat"
    r"|\bDEC-\d+|agents-workflow|\brelay\b|integration-orch|infra-orch|platform-orch|general orchestrator|area orchestrator"
    r"|\bate-<n>|merge packet|root=|\bROOT\b|\bscribe\b", re.IGNORECASE)


def herdr_entry() -> dict:
    plugins = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"]
    return next(p for p in plugins if p["name"] == "herdr")


class HerdrDependencyTest(unittest.TestCase):
    def test_marketplace_pins_the_release_commit(self) -> None:
        source = herdr_entry()["source"]
        self.assertEqual(source["source"], "git-subdir")
        self.assertEqual((source["url"], source["path"], source["ref"]), ("https://github.com/herdrdev/herdr.git", "skills/herdr", "v0.9.5"))
        self.assertRegex(source["sha"], SHA)
        self.assertEqual(source["sha"], "2ecf19a92fc3a7fff75b6ce3655ef04f4625ec01")

    def test_pai_console_has_no_dependency_and_pai_orchestration_depends_on_herdr(self) -> None:
        # A herdr fetch problem must never disable the Pai MCP or skills, so only pai-orchestration depends on it.
        console = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertNotIn("dependencies", console)
        plugins = {p["name"]: p for p in json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"]}
        self.assertEqual(plugins["pai-console"]["source"], "./")
        self.assertNotIn("dependencies", plugins["pai-console"])
        entry = plugins["pai-orchestration"]
        manifest = json.loads((ROOT / entry["source"] / ".claude-plugin/plugin.json").read_text())
        self.assertEqual((manifest["name"], manifest["version"], manifest["dependencies"]), ("pai-orchestration", "0.1.0", ["herdr"]))
        self.assertEqual(entry["version"], manifest["version"])

    def test_orchestration_skill_is_not_part_of_pai_console_or_its_codex_packages(self) -> None:
        self.assertFalse((ROOT / "skills/orchestration").exists())
        self.assertEqual(sorted(p.as_posix() for p in (ROOT / "plugins/codex").glob("*/skills/orchestration")), [])

    def test_no_symlinks_anywhere(self) -> None:
        links = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                 if ".git" not in p.parts and p.is_symlink()]
        self.assertEqual(links, [])

    def test_wake_plugin_is_portable(self) -> None:
        base = ROOT / "herdr-plugins/orchestration-wake"
        manifest = tomllib.loads((base / "herdr-plugin.toml").read_text())
        self.assertEqual(manifest["id"], "pai.orchestration-wake")
        for event in manifest["events"]:
            self.assertTrue((base / event["command"][1]).is_file(), event)
        for path in (p for p in base.rglob("*") if p.is_file()):
            self.assertIsNone(LEAK.search(path.read_text()), path.name)
        for script in ("bin/pai-pane-meta", "hooks/wake.sh", "hooks/deliver.sh"):
            self.assertTrue((base / script).stat().st_mode & 0o111, f"{script} must stay executable")
        self.assertIn("HERDR_BIN_PATH", (base / "hooks/wake.sh").read_text())

    def test_orchestration_skill_has_no_machine_specifics(self) -> None:
        plugin = ROOT / "plugins/orchestration"
        for path in plugin.rglob("*"):
            if path.is_file():
                self.assertIsNone(LEAK.search(path.read_text()), path.name)
        # The plugin is installed on its own: it must not cite files outside its own directory.
        skill = (plugin / "skills/orchestration/SKILL.md").read_text()
        self.assertNotRegex(skill, r"`\.\./")


class VendorDriftTest(unittest.TestCase):
    def copy_tree(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for name in (".claude-plugin", "vendor"):
            shutil.copytree(ROOT / name, tmp / name)
        return tmp

    def test_vendored_files_match_their_record(self) -> None:
        files = build_codex.herdr_vendor(ROOT)
        record = json.loads((ROOT / "vendor/herdr/PROVENANCE.json").read_text())
        self.assertEqual(hashlib.sha256(files[Path("skills/herdr/SKILL.md")]).hexdigest(), record["files"]["skills/herdr/SKILL.md"])

    def test_edited_vendored_copy_fails(self) -> None:
        tmp = self.copy_tree()
        skill = tmp / "vendor/herdr/skills/herdr/SKILL.md"
        skill.write_text(skill.read_text() + "\nlocal edit\n")
        with self.assertRaisesRegex(ValueError, "sha256"):
            build_codex.herdr_vendor(tmp)

    def test_bumped_pin_without_refresh_fails(self) -> None:
        tmp = self.copy_tree()
        path = tmp / ".claude-plugin/marketplace.json"
        data = json.loads(path.read_text())
        next(p for p in data["plugins"] if p["name"] == "herdr")["source"]["sha"] = "0" * 40
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "differs from the marketplace pin"):
            build_codex.herdr_vendor(tmp)


if __name__ == "__main__":
    unittest.main()
