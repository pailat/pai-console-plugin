"""deliver.sh ssh options and remote PATH, and the agent-keyed token cache of pai-pane-meta and wake.sh."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "herdr-plugins/orchestration-wake"
DELIVER = PLUGIN / "hooks/deliver.sh"
WAKE = PLUGIN / "hooks/wake.sh"
META = PLUGIN / "bin/pai-pane-meta"
SSH_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >>"$STUB_DIR/ssh.log"
exit 0
"""
HERDR_STUB = """#!/usr/bin/env bash
case "$1 $2" in
  "pane get") cat "$STUB_DIR/pane.json" ;;
  "agent get") cat "$STUB_DIR/agent-$(printf %s "$3" | tr -c 'A-Za-z0-9' _).json" 2>/dev/null; exit 0 ;;
  "agent prompt") printf 'prompt\\t%s\\t%s\\n' "$3" "$4" >>"$STUB_DIR/calls.log" ;;
  "pane report-metadata") printf 'meta\\t%s\\n' "$3" >>"$STUB_DIR/calls.log" ;;
esac
exit 0
"""


def key(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text)


@unittest.skipUnless(shutil.which("jq") and shutil.which("bash"), "the wake plugin needs bash and jq")
class WakeDeliveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        for name, body in (("ssh", SSH_STUB), ("herdr", HERDR_STUB)):
            (self.dir / name).write_text(body)
            (self.dir / name).chmod(0o755)
        for sub in ("state", "config"):
            (self.dir / sub).mkdir()

    def env(self, **extra: str) -> dict[str, str]:
        return {"PATH": f"{self.dir}:{os.environ['PATH']}", "HERDR_BIN_PATH": str(self.dir / "herdr"), "STUB_DIR": str(self.dir),
                "HERDR_PLUGIN_STATE_DIR": str(self.dir / "state"), "HERDR_PLUGIN_CONFIG_DIR": str(self.dir / "config"),
                "PAI_WAKE_HOSTS": "far=far-host", **extra}

    def deliver(self, **extra: str) -> str:
        subprocess.run(["bash", str(DELIVER), "far:boss", "wake: done"], env=self.env(**extra), check=True, capture_output=True, timeout=60)
        log = self.dir / "ssh.log"
        return log.read_text().strip() if log.exists() else ""

    def wake_log(self) -> str:
        path = self.dir / "state/wake.log"
        return path.read_text() if path.exists() else ""

    def test_default_ssh_options_are_batch_mode_with_a_timeout(self) -> None:
        self.assertTrue(self.deliver().startswith("-o BatchMode=yes -o ConnectTimeout=8 far-host "))

    def test_custom_ssh_options_replace_the_defaults(self) -> None:
        line = self.deliver(PAI_WAKE_SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=3 -i /tmp/example-identity")
        self.assertTrue(line.startswith("-o BatchMode=yes -o ConnectTimeout=3 -i /tmp/example-identity far-host "), line)
        self.assertNotIn("ConnectTimeout=8", line)

    def test_a_valid_remote_path_prefixes_the_remote_herdr_call(self) -> None:
        line = self.deliver(PAI_WAKE_REMOTE_PATH="~/bin:/opt/example/bin")
        # The call is quoted once for the remote login shell, so spaces and the literal $PATH arrive escaped.
        self.assertIn("PATH=\\~/bin:/opt/example/bin:\\$PATH\\ herdr\\ agent\\ prompt\\ boss", line)

    def test_an_invalid_remote_path_is_refused_and_logged_but_the_wake_is_still_sent(self) -> None:
        line = self.deliver(PAI_WAKE_REMOTE_PATH="/x;touch /tmp/example-injected")
        self.assertNotIn("PATH=", line)
        self.assertNotIn("injected", line)
        self.assertIn("herdr\\ agent\\ prompt\\ boss", line)
        self.assertIn("PAI_WAKE_REMOTE_PATH", self.wake_log())

    def test_pane_meta_writes_the_agent_keyed_cache_and_removes_the_old_pane_file(self) -> None:
        old = self.dir / "config/panes"
        old.mkdir()
        (old / "w1_p2.json").write_text(json.dumps({"tokens": {"role": "lead"}}))
        subprocess.run(["bash", str(META), "w1:p2", "role=lead", "name=child/one", "parent=boss"], env=self.env(), check=True, capture_output=True, timeout=60)
        written = json.loads((self.dir / "config/agents/child_one.json").read_text())
        self.assertEqual(written, {"pane": "w1:p2", "tokens": {"role": "lead", "name": "child/one", "parent": "boss"}})
        self.assertFalse((old / "w1_p2.json").exists())

    def test_a_pane_without_a_name_token_is_keyed_by_its_pane_id(self) -> None:
        subprocess.run(["bash", str(META), "w1:p9", "role=lead", "parent=boss"], env=self.env(), check=True, capture_output=True, timeout=60)
        self.assertEqual(json.loads((self.dir / "config/agents/pane-w1_p9.json").read_text())["pane"], "w1:p9")

    def fire(self, pane: str, status: str) -> None:
        payload = {"event": "pane_agent_status_changed", "data": {"type": "pane.agent_status_changed", "pane_id": pane, "agent_status": status}}
        subprocess.run(["bash", str(WAKE)], env=self.env(HERDR_PLUGIN_EVENT_JSON=json.dumps(payload), PAI_WAKE_MIN_INTERVAL="0"),
                       check=True, capture_output=True, timeout=60)

    def prompts(self) -> list[str]:
        log = self.dir / "calls.log"
        return [row.split("\t")[1] for row in log.read_text().splitlines() if row.startswith("prompt")] if log.exists() else []

    def test_wake_finds_the_agent_keyed_cache_by_its_pane_field(self) -> None:
        # No live tokens: Herdr dropped them, so only the cache can say who the parent is.
        (self.dir / "pane.json").write_text(json.dumps({"result": {"pane": {}}}))
        agents = self.dir / "config/agents"
        agents.mkdir()
        (agents / "other.json").write_text(json.dumps({"pane": "w1:p7", "tokens": {"role": "lead", "parent": "elsewhere", "wake_on_done": "1"}}))
        (agents / "child.json").write_text(json.dumps({"pane": "w1:p2", "tokens": {"role": "lead", "issue": "T-1", "name": "child", "parent": "boss", "wake_on_done": "1"}}))
        self.fire("w1:p2", "working")
        self.fire("w1:p2", "done")
        self.assertEqual(self.prompts(), ["boss"])

    def test_wake_falls_back_to_the_old_pane_keyed_cache(self) -> None:
        (self.dir / "pane.json").write_text(json.dumps({"result": {"pane": {}}}))
        old = self.dir / "config/panes"
        old.mkdir()
        (old / "w1_p2.json").write_text(json.dumps({"tokens": {"role": "lead", "issue": "T-1", "name": "child", "parent": "boss", "wake_on_done": "1"}}))
        self.fire("w1:p2", "working")
        self.fire("w1:p2", "done")
        self.assertEqual(self.prompts(), ["boss"])

    def meta(self, pane: str, *tokens: str) -> None:
        subprocess.run(["bash", str(META), pane, *tokens], env=self.env(), check=True, capture_output=True, timeout=60)

    def test_a_mutual_pair_does_not_ping_pong_when_live_tokens_are_gone(self) -> None:
        # After a Herdr restart only the agent-keyed cache knows each pane's parent, so the loop guard must read it too.
        (self.dir / "pane.json").write_text(json.dumps({"result": {"pane": {}}}))
        for name, pane, parent in (("pane-a", "w1:p2", "pane-b"), ("pane-b", "w1:p3", "pane-a")):
            self.meta(pane, "role=lead", f"name={name}", f"parent={parent}", "wake_on_done=1", "issue=T-1")
            (self.dir / f"agent-{key(name)}.json").write_text(json.dumps({"result": {"agent": {"pane_id": pane}}}))
        for _ in range(2):
            for pane in ("w1:p2", "w1:p3"):
                self.fire(pane, "working")
                self.fire(pane, "done")
        self.assertEqual(self.prompts(), [])
        self.assertIn("(loop)", self.wake_log())

    def test_a_second_pane_meta_call_for_the_same_pane_leaves_one_cache_file(self) -> None:
        self.meta("w1:p9", "role=lead", "parent=boss")
        self.meta("w1:p9", "role=lead", "name=x", "parent=boss")
        files = sorted(p.name for p in (self.dir / "config/agents").glob("*.json"))
        self.assertEqual(files, ["x.json"])

    def test_another_agents_cache_file_is_left_alone(self) -> None:
        self.meta("w1:p8", "role=lead", "name=other", "parent=boss")
        self.meta("w1:p9", "role=lead", "name=x", "parent=boss")
        self.assertEqual(sorted(p.name for p in (self.dir / "config/agents").glob("*.json")), ["other.json", "x.json"])


if __name__ == "__main__":
    unittest.main()
