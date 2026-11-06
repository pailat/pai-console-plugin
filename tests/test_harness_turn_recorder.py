"""turn-recorder: a fixture event goes in, journal lines come out, and a replay adds nothing."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins/pai-harness/herdr-plugins/turn-recorder"
HOOK = PLUGIN / "hooks/record.py"
FIXTURES = ROOT / "tests/fixtures/harness-wake"
HERDR_STUB = """#!/usr/bin/env bash
[ "$1 $2" = "pane get" ] && cat "$STUB_DIR/pane.json"
exit 0
"""


class TurnRecorderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        stub = self.dir / "herdr"
        stub.write_text(HERDR_STUB)
        stub.chmod(0o755)
        for sub in ("state", "config"):
            (self.dir / sub).mkdir()
        self.stream = self.dir / "run.jsonl"
        self.events = json.loads((FIXTURES / "turn-events.json").read_text())
        self.pane({"name": "child", "stream": str(self.stream)})

    def pane(self, tokens: dict) -> None:
        (self.dir / "pane.json").write_text(json.dumps({"result": {"pane": {"tokens": tokens, "label": "child"}}}))

    def fire(self, event: dict, **extra: str) -> None:
        env = {"PATH": os.environ["PATH"], "HERDR_BIN_PATH": str(self.dir / "herdr"), "STUB_DIR": str(self.dir),
               "HERDR_PLUGIN_STATE_DIR": str(self.dir / "state"), "HERDR_PLUGIN_CONFIG_DIR": str(self.dir / "config"),
               "HERDR_PLUGIN_EVENT_JSON": json.dumps(event), **extra}
        subprocess.run([sys.executable, str(HOOK)], env=env, check=True, capture_output=True, timeout=60)

    def journals(self) -> dict[str, list[dict]]:
        return {p.name: [json.loads(line) for line in p.read_text().splitlines()] for p in sorted((self.dir / "state/turns").glob("*.jsonl"))}

    def lines(self) -> list[dict]:
        return [line for rows in self.journals().values() for line in rows]

    def test_manifest_subscribes_to_both_events(self) -> None:
        manifest = tomllib.loads((PLUGIN / "herdr-plugin.toml").read_text())
        self.assertEqual(manifest["id"], "pai.turn-recorder")
        self.assertEqual({e["on"] for e in manifest["events"]}, {"pane.agent_status_changed", "pane.exited"})
        for event in manifest["events"]:
            self.assertTrue((PLUGIN / event["command"][-1]).is_file())

    def test_an_event_becomes_one_journal_line_with_a_key(self) -> None:
        self.fire(self.events[0])
        (name, rows), = self.journals().items()
        self.assertEqual(name, "w1_p2-0001.jsonl")
        self.assertEqual([(r["kind"], r["turn"], r["name"], r["data"]["agent_status"]) for r in rows], [("event", 1, "child", "working")])
        self.assertEqual(len(rows[0]["key"]), 32)

    def test_stream_frames_land_in_the_turn_file_after_the_event(self) -> None:
        shutil.copy(FIXTURES / "stream.jsonl", self.stream)
        self.fire(self.events[0])
        rows = self.lines()
        self.assertEqual([r["kind"] for r in rows], ["event"] + ["frame"] * 4)
        self.assertEqual(rows[1]["data"]["subtype"], "init")
        self.assertEqual(rows[4]["data"]["type"], "result")

    def test_a_run_is_one_file_per_turn_and_a_new_working_opens_the_next_turn(self) -> None:
        for event in self.events:
            self.fire(event)
        self.fire(self.events[0])  # the next turn starts
        self.assertEqual(sorted(self.journals()), ["w1_p2-0001.jsonl", "w1_p2-0002.jsonl"])
        first = [r["data"].get("agent_status", "exit") for r in self.journals()["w1_p2-0001.jsonl"]]
        self.assertEqual(first, ["working", "blocked", "working", "done", "exit"])

    def test_a_redelivered_event_adds_no_line(self) -> None:
        for event in self.events:
            self.fire(event)
        before = self.lines()
        for event in (self.events[3], self.events[4]):
            self.fire(event)
        self.assertEqual(self.lines(), before)

    def test_replaying_the_stream_adds_no_frame_and_new_frames_are_appended_once(self) -> None:
        shutil.copy(FIXTURES / "stream.jsonl", self.stream)
        self.fire(self.events[0])
        self.fire(self.events[1])
        with open(self.stream, "a") as handle:
            handle.write('{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"More."}]}}\n')
        self.fire(self.events[3])
        self.fire(self.events[4])
        frames = [r for r in self.lines() if r["kind"] == "frame"]
        self.assertEqual(len(frames), 5)
        keys = [r["key"] for r in self.lines()]
        self.assertEqual(len(keys), len(set(keys)))
        # Losing the recorder offset (a state wipe) must not duplicate frames either: the seen keys hold.
        state = self.dir / "state/pane-w1_p2.json"
        data = json.loads(state.read_text())
        data["offset"] = 0
        state.write_text(json.dumps(data))
        self.fire(self.events[4])
        self.assertEqual(len(self.lines()), len(keys))

    def test_events_with_their_own_id_are_idempotent_across_a_whole_replay(self) -> None:
        stamped = [{**e, "data": {**e["data"], "id": f"evt-{i}"}} for i, e in enumerate(self.events)]
        for event in stamped:
            self.fire(event)
        before = self.lines()
        for event in stamped:
            self.fire(event)
        self.assertEqual(self.lines(), before)

    def test_a_trailing_partial_line_waits_for_its_newline_until_the_turn_ends(self) -> None:
        self.stream.write_text('{"type":"system"}\n{"type":"assis')
        self.fire(self.events[0])
        self.assertEqual(len([r for r in self.lines() if r["kind"] == "frame"]), 1)
        self.fire(self.events[3])
        frames = [r for r in self.lines() if r["kind"] == "frame"]
        self.assertEqual(frames[1]["data"], {"raw": '{"type":"assis'})

    def test_the_stream_path_comes_from_config_when_the_pane_has_no_token(self) -> None:
        self.pane({"name": "child"})
        shutil.copy(FIXTURES / "stream.jsonl", self.dir / "child.jsonl")
        self.fire(self.events[0], PAI_RECORDER_STREAM=str(self.dir) + "/{name}.jsonl")
        self.assertEqual(len([r for r in self.lines() if r["kind"] == "frame"]), 4)

    def test_the_stream_path_is_remembered_for_pane_exited_when_herdr_has_dropped_the_tokens(self) -> None:
        shutil.copy(FIXTURES / "stream.jsonl", self.stream)
        self.fire(self.events[0])
        self.pane({})
        with open(self.stream, "a") as handle:
            handle.write('{"type":"result","subtype":"success"}\n')
        self.fire(self.events[4])
        self.assertEqual(len([r for r in self.lines() if r["kind"] == "frame"]), 5)

    def test_bad_input_never_fails_the_hook(self) -> None:
        self.fire({"event": "pane_exited", "data": {}})
        self.fire({"event": "something_else", "data": {"pane_id": "w1:p2"}})
        subprocess.run([sys.executable, str(HOOK)], env={"PATH": os.environ["PATH"], "HERDR_PLUGIN_STATE_DIR": str(self.dir / "state"),
                       "HERDR_PLUGIN_EVENT_JSON": "not json"}, check=True, capture_output=True, timeout=60)
        self.assertEqual(self.lines(), [])


if __name__ == "__main__":
    unittest.main()
