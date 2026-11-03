"""The single pai-console plugin: vendored Herdr skill, orchestration skill, wake plugin, release-watch workflow and no symlinks."""

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
# One leak guard for everything this repository publishes about orchestration (the wake plugin and the skill).
# Generic patterns catch machine, path, network and contact identifiers. Internal names, roles, process terms and decision-id
# prefixes are not spelled out here: INTERNAL holds sha256 digests of the lowercased tokens (and adjacent word pairs) to refuse.
LEAK = re.compile(
    r"/home/|/Users/|~/worktrees|\bw[A-Z]{2}:p[0-9A-Z]+|\b100\.\d+\.\d+\.\d+|\.ts\.net|[\w.+-]+@[\w-]+\.[\w.]+")
INTERNAL = frozenset((
    "0f7b552c61ce21cb21441b18aada8dadbf6d9b833889bc8b3c77b40423280f08",
    "0fd92a2b7a7fdef742fdce069208e45fd836888c35ed04c6296e54ffb168e78f",
    "1e97fe35a5a57e7d6a782a3194e0d9a90e59862fc8f3e353cd20651124b4e9f0",
    "25b5234dbbdcbd0d0d0a088fdfaef691b2003828e4e683c0255a16d20225507d",
    "26b47209413e5776b8a32b9ef89bb47312a75875bf475d39a78e5ae4dcc095f3",
    "367cf9147ab7a8fe3fc6ff1a3e391e34e0ac0a2cdae25a80f08c1d49134bbc4c",
    "382a803dcc0de9618b141c904dde30f933985956df74ce7fd9886494c7a35a60",
    "414360a5214ca1a5e3e78daab9eaa98f4cda5eae68345148afc153d0f515d5f1",
    "41957a1c93a194b3b0fec10164d817a742ed20373c0ebf513b1a1f59c71a49cb",
    "4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2",
    "516e4c8d17f2cd77e3e81cf84b11784f62cc2dd215f7e23635d2546646b3ecdd",
    "56c802d0a7a022c33453498e5c30ba2f565b289f0f2ac31c1b0b3bb62e1c2d56",
    "682fbae20f3428bcec4c117c57bea18d438c4758d972909b41dbe22884e0d6b8",
    "86e3ac0aa93915d8ceff42620cbc067c0dd7b2d83619c0f43eaa5d5bc2179ab7",
    "92c28e6f476bc04ebfad33c9f31b224dae025c191fbeb9ad66fb412b37ae86f1",
    "bb8d3e48afb09ba7e1aeb83a7949927901d77e9431100d0f6ceb3e4f1cd942d3",
    "e325f3f34bc1a0f215b85cda02a3a46886f953d637e18cc0ac2046e2f3b22118",
    "e7502c799b8f76fbed077ff2cd55c906ab144d5b88ef09a71abc70b5fad601f1",
    "e8d6382f98ac2855f4cadf2d3bb63aded7bfbe8c200a867f4ea6da47bb016bd3",
    "f31c99ff1c32090771b7288b20c9990b88fa0592e6899de8bf0629168072c4fa",
    "ff7fce673d2f52b071129e34ff8ea570b7159527d019c81ec7756f4f8c821535",
    "ffb301e28a65f3046dd636ef12d04f8d2fc2e2b3b0001b0d88ce5e770dbca2da",
))
WORD = re.compile(r"[a-z0-9<>][a-z0-9<>_=-]*")


def leaks(text: str, internal: frozenset[str] = INTERNAL) -> list[str]:
    """Return what in the text is a generic leak or hashes to a refused internal term."""
    found = [m.group(0) for m in LEAK.finditer(text)]
    words = [w.strip("-") for w in WORD.findall(text.lower())]
    candidates = set(words) | {" ".join(pair) for pair in zip(words, words[1:])}
    candidates |= {re.sub(r"-\d+$", "", w) for w in words if re.search(r"-\d+$", w)}  # decision-style ids: hash the prefix
    candidates |= {w.split("-<")[0] + "-<n>" for w in words if "-<" in w}
    return found + sorted(c for c in candidates if hashlib.sha256(c.encode()).hexdigest() in internal)


def pai_console_files() -> list[Path]:
    return [p for p in (ROOT / "skills/orchestration").rglob("*") if p.is_file()]


class SinglePluginTest(unittest.TestCase):
    def test_the_vendored_herdr_pin_is_the_release_commit(self) -> None:
        pin = json.loads((ROOT / "vendor/herdr/PIN.json").read_text())
        self.assertEqual((pin["repository"], pin["path"], pin["tag"]), ("https://github.com/herdrdev/herdr", "skills/herdr", "v0.9.5"))
        self.assertRegex(pin["commit"], SHA)
        self.assertEqual(pin["commit"], "2ecf19a92fc3a7fff75b6ce3655ef04f4625ec01")

    def test_pai_console_is_the_only_plugin_and_has_no_dependencies(self) -> None:
        console = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertNotIn("dependencies", console)
        self.assertEqual(console["version"], "0.0.12")
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual([p["name"] for p in marketplace["plugins"]], ["pai-console"])
        self.assertEqual(marketplace["plugins"][0]["source"], "./")
        self.assertNotIn("dependencies", marketplace["plugins"][0])
        self.assertFalse((ROOT / "plugins/orchestration").exists())

    def test_removed_plugins_are_migrated_and_cleaned_up_from_installed_copies(self) -> None:
        # marketplace-reference "Top-level fields" and host-marketplace "Rename or remove a plugin": a null rename drops the
        # old key from settings, forceRemoveDeletedPlugins uninstalls the copy.
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(marketplace["renames"], {"pai-orchestration": None, "herdr": None})
        self.assertIs(marketplace["forceRemoveDeletedPlugins"], True)

    def test_herdr_and_orchestration_ship_in_pai_console_and_every_codex_package_for_explicit_use_only(self) -> None:
        for name in ("herdr", "orchestration"):
            self.assertTrue((ROOT / f"skills/{name}/SKILL.md").is_file(), name)
            packaged = sorted((ROOT / "plugins/codex").glob(f"*/skills/{name}/SKILL.md"))
            self.assertEqual(len(packaged), 3, name)
            for skill in packaged:
                self.assertEqual((skill.parent / "agents/openai.yaml").read_text(), "policy:\n  allow_implicit_invocation: false\n")
                self.assertEqual(skill.read_bytes(), (ROOT / f"skills/{name}/SKILL.md").read_bytes())

    def test_the_skills_trigger_only_on_explicit_herdr_work(self) -> None:
        for name in ("herdr", "orchestration"):
            front = (ROOT / f"skills/{name}/SKILL.md").read_text().split("---")[1]
            description = re.search(r'^description: "(.*)"$', front, re.M).group(1)
            self.assertRegex(description.lower(), r"use only when|explicitly", name)
            self.assertNotRegex(description.lower(), r"\bany pai task\b|\balways\b", name)
        self.assertIn("Do not use for ordinary Pai tasks", (ROOT / "skills/orchestration/SKILL.md").read_text())

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
            self.assertEqual(leaks(path.read_text()), [], path.name)
        for script in ("bin/pai-pane-meta", "hooks/wake.sh", "hooks/deliver.sh"):
            self.assertTrue((base / script).stat().st_mode & 0o111, f"{script} must stay executable")
        self.assertIn("HERDR_BIN_PATH", (base / "hooks/wake.sh").read_text())

    def test_orchestration_skill_has_no_machine_specifics(self) -> None:
        # The skill reaches every pai-console install, clients included, so it must stay generic.
        for path in pai_console_files():
            self.assertEqual(leaks(path.read_text()), [], path.name)


class VendorDriftTest(unittest.TestCase):
    def copy_tree(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        shutil.copytree(ROOT / "vendor", tmp / "vendor")
        shutil.copytree(ROOT / "skills/herdr", tmp / "skills/herdr")
        return tmp

    def test_vendored_files_match_their_record(self) -> None:
        files = build_codex.herdr_vendor(ROOT)
        record = json.loads((ROOT / "vendor/herdr/PROVENANCE.json").read_text())
        self.assertEqual(files, record["files"])
        self.assertEqual(hashlib.sha256((ROOT / "skills/herdr/SKILL.md").read_bytes()).hexdigest(), record["files"]["SKILL.md"])

    def test_the_package_build_still_runs_the_drift_check(self) -> None:
        tmp = self.copy_tree()
        skill = tmp / "skills/herdr/SKILL.md"
        skill.write_text(skill.read_text() + "\nlocal edit\n")
        with self.assertRaisesRegex(ValueError, "sha256"):
            build_codex.expected_files(tmp)

    def test_edited_vendored_copy_fails(self) -> None:
        tmp = self.copy_tree()
        skill = tmp / "skills/herdr/SKILL.md"
        skill.write_text(skill.read_text() + "\nlocal edit\n")
        with self.assertRaisesRegex(ValueError, "sha256"):
            build_codex.herdr_vendor(tmp)

    def test_an_extra_vendored_file_fails(self) -> None:
        tmp = self.copy_tree()
        (tmp / "skills/herdr/NOTES.md").write_text("hand written")
        with self.assertRaisesRegex(ValueError, "differ from PROVENANCE"):
            build_codex.herdr_vendor(tmp)

    def test_bumped_pin_without_refresh_fails(self) -> None:
        tmp = self.copy_tree()
        path = tmp / "vendor/herdr/PIN.json"
        data = json.loads(path.read_text())
        data["commit"] = "0" * 40
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "differs from the pin"):
            build_codex.herdr_vendor(tmp)


class ReleaseWatchWorkflowTest(unittest.TestCase):
    """The scheduled Action only vendors through the tool and opens a pull request: least privilege, pinned actions, no merge."""

    def setUp(self) -> None:
        self.text = (ROOT / ".github/workflows/herdr-release-watch.yml").read_text()
        import yaml
        self.workflow = yaml.safe_load(self.text)

    def test_it_is_scheduled_and_has_minimal_permissions(self) -> None:
        self.assertIn("schedule", self.workflow[True])
        self.assertEqual(self.workflow["permissions"], {"contents": "write", "pull-requests": "write"})
        self.assertNotIn("pull_request_target", self.workflow[True])

    def test_every_third_party_action_is_pinned_by_commit(self) -> None:
        uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)", self.text, re.M)
        self.assertTrue(uses)
        for ref in uses:
            self.assertRegex(ref, r"@[0-9a-f]{40}$", ref)

    def test_it_vendors_through_the_tool_and_never_merges(self) -> None:
        self.assertIn("python3 tools/vendor_herdr.py --latest", self.text)
        self.assertIn("gh pr create", self.text)
        # Without the repository setting the job must fail visibly, naming it.
        self.assertRegex(self.text, r"if ! gh pr create")
        self.assertIn("::error", self.text)
        self.assertIn("Allow GitHub Actions to create and approve pull requests", self.text)
        self.assertNotRegex(self.text, r"gh pr merge|--auto|enable-auto-merge|--admin|--force")
        self.assertEqual(leaks(self.text), [])


class LeakGuardTest(unittest.TestCase):
    def test_the_guard_detects_generic_leaks(self) -> None:
        for text in ("see /home/someone/x", "ssh to 100.64.1.2", "mail someone@example.com", "pane wAB:p12", "host.example.ts.net"):
            with self.subTest(text=text):
                self.assertTrue(leaks(text))
        self.assertEqual(leaks("never go idle; report to the parent named in the brief"), [])

    def test_the_guard_matches_words_pairs_and_id_prefixes_by_digest(self) -> None:
        digest = lambda term: hashlib.sha256(term.encode()).hexdigest()  # noqa: E731
        internal = frozenset({digest("zzterm"), digest("two words"), digest("zzid"), digest("zzcase-<n>")})
        self.assertEqual(leaks("Ask the ZZTERM, then stop.", internal), ["zzterm"])
        self.assertEqual(leaks("these two words here", internal), ["two words"])
        self.assertEqual(leaks("see ZZID-042 now", internal), ["zzid"])
        self.assertEqual(leaks("zzcase-<n>-lead", internal), ["zzcase-<n>"])
        self.assertEqual(leaks("nothing refused here", internal), [])
        self.assertTrue(INTERNAL and all(len(d) == 64 for d in INTERNAL))



if __name__ == "__main__":
    unittest.main()
