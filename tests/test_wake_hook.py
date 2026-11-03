"""wake.sh drives only real wakes: no self-target, no lost wakes between children, no ping-pong, no option injection."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WAKE = ROOT / "herdr-plugins/orchestration-wake/hooks/wake.sh"
STUB = """#!/usr/bin/env bash
key() { printf %s "$1" | tr -c 'A-Za-z0-9' _; }
case "$1 $2" in
  "pane get") f="$STUB_DIR/pane-$(key "$3").json"; [ -f "$f" ] && cat "$f" || cat "$STUB_DIR/pane.json" ;;
  "agent get") cat "$STUB_DIR/agent-$(key "$3").json" 2>/dev/null ;;
  "agent prompt") printf 'prompt\\t%s\\t%s\\n' "$3" "$4" >>"$STUB_DIR/calls.log" ;;
  "notification show") printf 'notify\\t%s\\n' "$3" >>"$STUB_DIR/calls.log" ;;
esac
exit 0
"""


def key(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text)


@unittest.skipUnless(shutil.which("jq") and shutil.which("bash"), "wake.sh needs bash and jq")
class WakeHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        stub = self.dir / "herdr"
        stub.write_text(STUB)
        stub.chmod(0o755)
        for sub in ("state", "config/panes"):
            (self.dir / sub).mkdir(parents=True)

    def pane(self, name: str, parent: str, pane_id: str = "w1:p2") -> None:
        tokens = {"role": "lead", "issue": "T-1", "name": name, "parent": parent, "requester": parent, "wake_on_done": "1"}
        body = json.dumps({"result": {"pane": {"tokens": tokens, "label": name}}})
        (self.dir / "pane.json").write_text(body)
        (self.dir / f"pane-{key(pane_id)}.json").write_text(body)
        (self.dir / f"agent-{key(name)}.json").write_text(json.dumps({"result": {"agent": {"pane_id": pane_id}}}))
        (self.dir / "config/panes" / f"{key(pane_id)}.json").write_text(json.dumps({"tokens": tokens}))

    def fire(self, status: str, pane_id: str = "w1:p2", interval: str = "60", event: str = "pane.agent_status_changed", **extra: str) -> None:
        payload = {"event": event.replace(".", "_"), "data": {"type": event, "pane_id": pane_id, "agent_status": status}}
        env = {"PATH": os.environ["PATH"], "HERDR_BIN_PATH": str(self.dir / "herdr"), "STUB_DIR": str(self.dir),
               "HERDR_PLUGIN_STATE_DIR": str(self.dir / "state"), "HERDR_PLUGIN_CONFIG_DIR": str(self.dir / "config"),
               "HERDR_PLUGIN_EVENT_JSON": json.dumps(payload), "PAI_WAKE_MIN_INTERVAL": interval, **extra}
        subprocess.run(["bash", str(WAKE)], env=env, check=True, capture_output=True, timeout=60)

    def calls(self, kind: str = "prompt") -> list[list[str]]:
        log = self.dir / "calls.log"
        rows = [line.split("\t") for line in log.read_text().splitlines()] if log.exists() else []
        return [row for row in rows if row[0] == kind]

    def finish_cycle(self, pane_id: str = "w1:p2", **kwargs: str) -> None:
        self.fire("working", pane_id, **kwargs)
        self.fire("done", pane_id, **kwargs)

    def test_a_finished_child_wakes_its_parent(self) -> None:
        self.pane("child", "boss")
        self.finish_cycle()
        self.assertEqual([row[1] for row in self.calls()], ["boss"])

    def test_a_pane_never_wakes_itself(self) -> None:
        for parent in ("child", "w1:p2"):
            with self.subTest(parent=parent):
                (self.dir / "calls.log").unlink(missing_ok=True)
                self.pane("child", parent)
                self.finish_cycle(interval="0")
                self.assertEqual(self.calls(), [])

    def test_a_second_finish_of_the_same_pane_inside_the_interval_is_dropped(self) -> None:
        self.pane("child", "boss")
        self.finish_cycle()
        self.finish_cycle()
        self.assertEqual(len(self.calls()), 1)

    def test_two_children_finishing_inside_the_interval_both_wake_the_parent(self) -> None:
        self.pane("child-a", "boss", "w1:p2")
        self.pane("child-b", "boss", "w1:p3")
        self.finish_cycle("w1:p2")
        self.finish_cycle("w1:p3")
        self.assertEqual(sorted(row[2] for row in self.calls()), ["wake: child-a finished (T-1): read it", "wake: child-b finished (T-1): read it"])

    def test_blocked_and_exited_are_never_rate_limited(self) -> None:
        self.pane("child-a", "boss", "w1:p2")
        self.pane("child-b", "boss", "w1:p3")
        self.finish_cycle("w1:p2")
        self.fire("blocked", "w1:p2")
        self.fire("blocked", "w1:p3")
        self.fire("exited", "w1:p2", event="pane.exited")
        texts = [row[2] for row in self.calls()]
        self.assertEqual(len(texts), 4, texts)
        self.assertTrue(any("exited" in t for t in texts))
        self.assertEqual(sum("BLOCKED" in t for t in texts), 2)

    def test_a_mutual_pair_does_not_ping_pong(self) -> None:
        self.pane("pane-a", "pane-b", "w1:p2")
        self.pane("pane-b", "pane-a", "w1:p3")
        for _ in range(3):
            self.finish_cycle("w1:p2", interval="0")
            self.finish_cycle("w1:p3", interval="0")
        self.assertEqual(self.calls(), [])

    def test_a_pair_addressed_by_pane_id_does_not_ping_pong_either(self) -> None:
        self.pane("pane-a", "w1:p3", "w1:p2")
        self.pane("pane-b", "w1:p2", "w1:p3")
        self.finish_cycle("w1:p2", interval="0")
        self.finish_cycle("w1:p3", interval="0")
        self.assertEqual(self.calls(), [])

    def test_the_hourly_cap_per_source_and_target_stops_a_runaway(self) -> None:
        self.pane("child", "boss")
        for _ in range(5):
            self.finish_cycle(interval="0", PAI_WAKE_MAX_PER_HOUR="2")
        self.assertEqual(len(self.calls()), 2)

    def test_consecutive_blocked_events_prompt_once(self) -> None:
        self.pane("child", "boss")
        self.fire("blocked")
        self.fire("blocked")
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(len(self.calls("notify")), 1)
        self.fire("working")
        self.fire("blocked")
        self.assertEqual(len(self.calls()), 2)

    def test_a_dashed_pane_name_cannot_become_an_option(self) -> None:
        self.pane("--foo", "boss")
        self.finish_cycle()
        (row,) = self.calls()
        self.assertFalse(row[2].startswith("-"), row)
        self.fire("blocked")
        self.assertFalse(self.calls("notify")[0][1].startswith("-"))


if __name__ == "__main__":
    unittest.main()
