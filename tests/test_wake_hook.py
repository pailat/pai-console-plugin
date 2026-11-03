"""wake.sh drives only real wakes: no self-target, a per-target interval, no repeated blocked prompts, no option injection."""

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
case "$1 $2" in
  "pane get") cat "$STUB_DIR/pane.json" ;;
  "agent prompt") printf 'prompt\\t%s\\t%s\\n' "$3" "$4" >>"$STUB_DIR/calls.log" ;;
  "notification show") printf 'notify\\t%s\\n' "$3" >>"$STUB_DIR/calls.log" ;;
esac
exit 0
"""


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
        (self.dir / "pane.json").write_text(json.dumps({"result": {"pane": {"tokens": tokens, "label": name}}}))
        key = "".join(c if c.isalnum() else "_" for c in pane_id)
        (self.dir / "config/panes" / f"{key}.json").write_text(json.dumps({"tokens": tokens}))

    def fire(self, status: str, pane_id: str = "w1:p2", interval: str = "60") -> None:
        event = {"event": "pane_agent_status_changed", "data": {"type": "pane.agent_status_changed", "pane_id": pane_id, "agent_status": status}}
        env = {"PATH": os.environ["PATH"], "HERDR_BIN_PATH": str(self.dir / "herdr"), "STUB_DIR": str(self.dir),
               "HERDR_PLUGIN_STATE_DIR": str(self.dir / "state"), "HERDR_PLUGIN_CONFIG_DIR": str(self.dir / "config"),
               "HERDR_PLUGIN_EVENT_JSON": json.dumps(event), "PAI_WAKE_MIN_INTERVAL": interval}
        subprocess.run(["bash", str(WAKE)], env=env, check=True, capture_output=True, timeout=60)

    def calls(self, kind: str = "prompt") -> list[list[str]]:
        log = self.dir / "calls.log"
        rows = [line.split("\t") for line in log.read_text().splitlines()] if log.exists() else []
        return [row for row in rows if row[0] == kind]

    def finish_cycle(self, **kwargs: str) -> None:
        self.fire("working", **kwargs)
        self.fire("done", **kwargs)

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

    def test_a_second_wake_inside_the_interval_is_dropped(self) -> None:
        self.pane("child", "boss")
        self.finish_cycle()
        self.finish_cycle()
        self.assertEqual(len(self.calls()), 1)

    def test_with_a_zero_interval_each_finish_wakes(self) -> None:
        self.pane("child", "boss")
        self.finish_cycle(interval="0")
        self.finish_cycle(interval="0")
        self.assertEqual(len(self.calls()), 2)

    def test_consecutive_blocked_events_prompt_once(self) -> None:
        self.pane("child", "boss")
        self.fire("blocked", interval="0")
        self.fire("blocked", interval="0")
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(len(self.calls("notify")), 1)
        self.fire("working", interval="0")
        self.fire("blocked", interval="0")
        self.assertEqual(len(self.calls()), 2)

    def test_a_dashed_pane_name_cannot_become_an_option(self) -> None:
        self.pane("--foo", "boss")
        self.finish_cycle()
        (row,) = self.calls()
        self.assertFalse(row[2].startswith("-"), row)
        self.fire("blocked", interval="0")
        self.assertFalse(self.calls("notify")[0][1].startswith("-"))


if __name__ == "__main__":
    unittest.main()
