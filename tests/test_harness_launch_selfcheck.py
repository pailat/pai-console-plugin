"""The launcher proves the pai-harness plugin is loaded from the run's system/init event, and fails closed otherwise."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, PLUGIN_ROOT, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import harness_lib as lib  # noqa: E402


class SelfCheckTest(HarnessCase):
    def assert_fails_closed(self, done, *fragments: str) -> None:
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("BLOCKER ACME-7: pai-harness self-check failed", done.stdout)
        for fragment in fragments:
            self.assertIn(fragment, done.stdout)
        blockers = [e for e in self.journal() if e["kind"] == "BLOCKER"]
        self.assertEqual(len(blockers), 1)
        self.assertEqual(blockers[0]["line"], done.stdout.strip())
        self.assertEqual(self.record("ACME-7")["state"], "failed")

    def test_a_complete_init_event_passes(self) -> None:
        done = self.launch("ACME-7", "success")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertFalse([e for e in self.journal() if e["kind"] == "BLOCKER"])

    def test_a_missing_skill_fails_closed(self) -> None:
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt),
                               FAKE_CLAUDE_FIXTURE=str(self.fixture("success", drop_skill="pai-harness:lead")))
        self.assert_fails_closed(done, "skill pai-harness:lead not loaded")

    def test_a_missing_hook_fails_closed(self) -> None:
        plugin = self.tmp / "plugin"
        (plugin / "hooks").mkdir(parents=True)
        hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text())
        del hooks["hooks"]["Stop"]
        (plugin / "hooks/hooks.json").write_text(json.dumps(hooks))
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt),
                               FAKE_CLAUDE_FIXTURE=str(self.fixture("success", hooks_dir=plugin)))
        self.assert_fails_closed(done, "hook Stop not registered")

    def test_no_init_event_fails_closed(self) -> None:
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt),
                               FAKE_CLAUDE_FIXTURE=str(FIXTURES / "init_no_init.jsonl"))
        self.assert_fails_closed(done, "init event came after the first model frame")

    def test_a_run_that_ends_without_any_frame_fails_closed(self) -> None:
        empty = self.tmp / "empty.jsonl"
        empty.write_text("")
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), FAKE_CLAUDE_FIXTURE=str(empty))
        self.assert_fails_closed(done, "no init event before the run ended")

    def test_a_late_init_event_kills_the_run_by_its_pid(self) -> None:
        silent = self.tmp / "silent.jsonl"
        silent.write_text("")
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), FAKE_CLAUDE_FIXTURE=str(silent),
                               FAKE_CLAUDE_SLEEP="30", PAI_HARNESS_INIT_TIMEOUT="1")
        self.assert_fails_closed(done, "no init event within 1s")

    def test_a_plugin_missing_from_init_fails_closed(self) -> None:
        frames = [json.loads(line) for line in self.fixture("success").read_text().splitlines()]
        frames[0]["plugins"] = [p for p in frames[0]["plugins"] if p["name"] != "pai-harness"]
        broken = self.tmp / "broken.jsonl"
        broken.write_text("\n".join(json.dumps(f) for f in frames) + "\n")
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), FAKE_CLAUDE_FIXTURE=str(broken))
        self.assert_fails_closed(done, "plugin pai-harness is not in init plugins")


class PluginDirTest(HarnessCase):
    def argv(self) -> list[str]:
        return json.loads((self.tmp / "claude.json").read_text())["argv"]

    def test_the_plugin_dir_is_the_launchers_own_plugin_root(self) -> None:
        self.launch("ACME-7", "success")
        argv = self.argv()
        self.assertEqual(argv[argv.index("--plugin-dir") + 1], str(PLUGIN_ROOT))

    def test_an_installed_plugin_is_used_instead(self) -> None:
        installed = self.tmp / "installed.json"
        installed.write_text(json.dumps({"version": 2, "plugins": {"pai-harness@pai": [{"scope": "user"}]}}))
        self.launch("ACME-7", "success", 0, PAI_HARNESS_INSTALLED_PLUGINS=str(installed))
        self.assertNotIn("--plugin-dir", self.argv())

    def test_expected_skills_come_from_the_skills_directory(self) -> None:
        self.assertIn("pai-harness:lead", lib.expected_skills(PLUGIN_ROOT))
        self.assertEqual(len(lib.expected_skills(PLUGIN_ROOT)), len(list((PLUGIN_ROOT / "skills").glob("*/SKILL.md"))))


if __name__ == "__main__":
    unittest.main()
