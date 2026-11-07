"""Wake delivery to another machine uses `herdr --machine <label>`, never ssh; the old ssh settings only print a deprecation."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = (ROOT / "plugins/pai-harness/herdr-plugins/orchestration-wake", ROOT / "herdr-plugins/orchestration-wake")
FAIL_SSH = """#!/usr/bin/env bash
printf 'ssh executed: %s\\n' "$*" >>"$STUB_DIR/ssh-executed"
exit 99
"""
HERDR = """#!/usr/bin/env bash
printf '%s\\n' "$*" >>"$STUB_DIR/herdr.log"
exit 0
"""


@unittest.skipUnless(shutil.which("jq") and shutil.which("bash"), "the wake plugin needs bash and jq")
class WakeMachineDeliveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        for name, body in (("ssh", FAIL_SSH), ("herdr", HERDR)):  # a failing ssh comes first on PATH
            (self.dir / name).write_text(body)
            (self.dir / name).chmod(0o755)
        (self.dir / "state").mkdir()

    def deliver(self, plugin: Path, target: str = "far:boss", **extra: str) -> subprocess.CompletedProcess[str]:
        env = {"PATH": f"{self.dir}:{os.environ['PATH']}", "HERDR_BIN_PATH": str(self.dir / "herdr"), "STUB_DIR": str(self.dir),
               "HERDR_PLUGIN_STATE_DIR": str(self.dir / "state"), "HERDR_PLUGIN_CONFIG_DIR": str(self.dir / "config"), **extra}
        return subprocess.run(["bash", str(plugin / "hooks/deliver.sh"), target, "wake: done"], env=env, check=True,
                              capture_output=True, text=True, timeout=60)

    def herdr_calls(self) -> list[str]:
        log = self.dir / "herdr.log"
        return log.read_text().splitlines() if log.exists() else []

    def wake_log(self) -> str:
        path = self.dir / "state/wake.log"
        return path.read_text() if path.exists() else ""

    def assertNoSsh(self) -> None:
        self.assertFalse((self.dir / "ssh-executed").exists(), "ssh was executed")

    def test_a_remote_target_uses_herdr_machine_and_never_ssh(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=str(plugin.relative_to(ROOT))):
                (self.dir / "herdr.log").unlink(missing_ok=True)
                self.deliver(plugin, PAI_WAKE_MACHINES="far=acme-laptop")
                self.assertEqual(self.herdr_calls(), ["--machine acme-laptop agent prompt boss wake: done"])
                self.assertNoSsh()

    def test_a_pane_id_after_the_alias_keeps_its_colon(self) -> None:
        self.deliver(PLUGINS[0], "far:w1:p2", PAI_WAKE_MACHINES="far=acme-laptop other=acme-desktop")
        self.assertEqual(self.herdr_calls(), ["--machine acme-laptop agent prompt w1:p2 wake: done"])

    def test_a_local_target_has_no_machine_flag(self) -> None:
        self.deliver(PLUGINS[0], "boss", PAI_WAKE_MACHINES="far=acme-laptop")
        self.assertEqual(self.herdr_calls(), ["agent prompt boss wake: done"])
        self.assertNoSsh()

    def test_an_unsafe_machine_label_is_not_delivered(self) -> None:
        self.deliver(PLUGINS[0], PAI_WAKE_MACHINES="far=acme;touch")
        self.assertEqual(self.herdr_calls(), [])
        self.assertIn("invalid machine label", self.wake_log())
        self.assertNoSsh()

    def test_a_leading_dash_in_the_label_or_the_target_is_never_passed_to_herdr(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=str(plugin.relative_to(ROOT))):
                (self.dir / "state/wake.log").unlink(missing_ok=True)
                self.deliver(plugin, "far:boss", PAI_WAKE_MACHINES="far=--help")
                self.deliver(plugin, "far:-x", PAI_WAKE_MACHINES="far=acme-laptop")
                self.deliver(plugin, "-x", PAI_WAKE_MACHINES="far=acme-laptop")
                self.assertEqual(self.herdr_calls(), [])
                self.assertIn("invalid machine label", self.wake_log())
                self.assertIn("leading dash", self.wake_log())

    def test_an_unknown_alias_is_logged_and_never_delivered_locally(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=str(plugin.relative_to(ROOT))):
                (self.dir / "state/wake.log").unlink(missing_ok=True)
                result = self.deliver(plugin, "frar:boss", PAI_WAKE_MACHINES="far=acme-laptop")
                self.assertEqual(self.herdr_calls(), [])
                self.assertIn("unknown machine alias", self.wake_log())
                self.assertIn("unknown machine alias", result.stderr)
                self.assertNoSsh()

    def test_the_old_ssh_settings_print_a_deprecation_and_do_not_ssh(self) -> None:
        old = {"PAI_WAKE_HOSTS": "far=acme-host", "PAI_WAKE_SSH_OPTS": "-o BatchMode=yes", "PAI_WAKE_REMOTE_PATH": "~/bin"}
        for plugin in PLUGINS:
            with self.subTest(plugin=str(plugin.relative_to(ROOT))):
                (self.dir / "herdr.log").unlink(missing_ok=True)
                result = self.deliver(plugin, **old)
                self.assertIn("DEPRECATED", result.stderr)
                for name in old:
                    self.assertIn(name, result.stderr)
                self.assertIn("DEPRECATED", self.wake_log())
                self.assertEqual(self.herdr_calls(), [], "an old ssh alias must not be delivered at all")
                self.assertNoSsh()

    def test_the_old_settings_next_to_a_machines_mapping_still_deliver_with_herdr_machine(self) -> None:
        result = self.deliver(PLUGINS[0], PAI_WAKE_HOSTS="far=acme-host", PAI_WAKE_MACHINES="far=acme-laptop")
        self.assertIn("DEPRECATED", result.stderr)
        self.assertEqual(self.herdr_calls(), ["--machine acme-laptop agent prompt boss wake: done"])
        self.assertNoSsh()

    def test_wake_sh_reads_the_machines_setting_from_config_env(self) -> None:
        # The config.env whitelist must carry PAI_WAKE_MACHINES, or wake.sh would never export it to deliver.sh.
        for plugin in PLUGINS:
            text = (plugin / "hooks/wake.sh").read_text()
            self.assertRegex(text, r"PAI_WAKE_OUTBOX\|PAI_WAKE_MACHINES\|")

    def test_a_finished_child_wakes_a_remote_parent_through_wake_sh_without_ssh(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=str(plugin.relative_to(ROOT))):
                state = self.dir / "state"
                shutil.rmtree(state, True); state.mkdir()
                (self.dir / "herdr.log").unlink(missing_ok=True)
                config = self.dir / "config/agents"
                config.mkdir(parents=True, exist_ok=True)
                (config / "child.json").write_text(json.dumps({"pane": "w1:p2", "tokens": {
                    "role": "lead", "issue": "ACME-1", "name": "child", "parent": "far:boss", "wake_on_done": "1"}}))
                env = {"PATH": f"{self.dir}:{os.environ['PATH']}", "HERDR_BIN_PATH": str(self.dir / "herdr"), "STUB_DIR": str(self.dir),
                       "HERDR_PLUGIN_STATE_DIR": str(state), "HERDR_PLUGIN_CONFIG_DIR": str(self.dir / "config"),
                       "PAI_WAKE_MACHINES": "far=acme-laptop", "PAI_WAKE_MIN_INTERVAL": "0"}
                for status in ("working", "done"):
                    payload = {"event": "pane_agent_status_changed", "data": {"pane_id": "w1:p2", "agent_status": status}}
                    subprocess.run(["bash", str(plugin / "hooks/wake.sh")], env={**env, "HERDR_PLUGIN_EVENT_JSON": json.dumps(payload)},
                                   check=True, capture_output=True, timeout=60)
                self.assertIn("--machine acme-laptop agent prompt boss wake: child finished (ACME-1): read it", self.herdr_calls())
                self.assertNoSsh()


class NoSshInstructionsTest(unittest.TestCase):
    """No maintained .md/.sh/.py under plugins/pai-harness tells an agent to ssh; the word appears only in a refusal or a deny rule."""

    NEGATION = re.compile(r"\b(never|not|no|without|refuse[sd]?|deny|denies|block(s|ed)?|forbid\w*)\b", re.I)
    # Policy code that names ssh in order to refuse or detect it.
    POLICY = {"hooks/pre_tool_use.py", "scripts/deny_baseline.py", "scripts/launch.py", "examples/settings.deny.json"}

    def scan(self, base: Path, policy: set[str]) -> list[str]:
        offenders = []
        for path in sorted(base.rglob("*")):
            if path.suffix not in {".md", ".sh", ".py"} or not path.is_file() or path.relative_to(base).as_posix() in policy:
                continue
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                if re.search(r"\bssh\b", line) and not self.NEGATION.search(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:120]}")
        return offenders

    def test_nothing_under_pai_harness_tells_an_agent_to_ssh(self) -> None:
        self.assertEqual(self.scan(ROOT / "plugins/pai-harness", self.POLICY), [])

    def test_the_root_wake_plugin_skills_and_codex_copies_do_not_tell_an_agent_to_ssh(self) -> None:
        bases = [ROOT / "herdr-plugins", ROOT / "skills", *sorted((ROOT / "plugins").glob("codex*"))]
        offenders = [o for base in bases if base.exists() for o in self.scan(base, self.POLICY)]
        self.assertEqual(offenders, [])

    def test_no_wake_script_runs_ssh_as_a_command(self) -> None:
        # Static scan: catches an absolute /usr/bin/ssh that the fake-ssh PATH trick cannot.
        command = re.compile(r"(^|[;&|(`]|\$\()\s*(/\S*/)?ssh(\s|$)|\b(exec|command|env|nohup|timeout\s+\d+)\s+(/\S*/)?ssh\b")
        offenders = []
        for plugin in PLUGINS:
            for path in sorted(plugin.rglob("*")):
                if path.is_file():
                    for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                        if not line.lstrip().startswith("#") and command.search(line):
                            offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:120]}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
