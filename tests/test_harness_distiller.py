"""The distiller plans a duplicate-free knowledge delta and writes the Stop-hook marker; the gate-triager names owner and next step."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "plugins/pai-harness"
FIXTURES = Path(__file__).resolve().parent / "fixtures/harness-distiller"
sys.path.insert(0, str(HARNESS / "scripts"))
sys.path.insert(0, str(HARNESS / "hooks"))
import delta_marker  # noqa: E402
import harness_config  # noqa: E402
import stop  # noqa: E402


def load(name: str):
    return json.loads((FIXTURES / name).read_text())


class DistillerTest(unittest.TestCase):
    def test_finished_task_yields_a_plan_without_duplicates(self) -> None:
        plan = delta_marker.plan(load("candidates.json"), load("existing-nodes.json"))
        self.assertEqual([n["ref"] for n in plan["create"]], ["$retry", "$clock"])
        self.assertEqual(plan["skipped"], [{"ref": "$swallow", "title": "Export client must not swallow 429 responses", "duplicate_of": "kn-acme-0007"}])
        self.assertEqual(plan["marker_hint"], ["kn-acme-0007"])
        decision = next(n for n in plan["create"] if n["kind"] == "decision")
        self.assertEqual(decision["status"], "proposed")

    def test_repeated_candidate_in_one_delta_is_created_once(self) -> None:
        data = load("candidates.json")
        data["nodes"].append({**data["nodes"][2], "ref": "$clock2", "title": "A retry test FAKES the clock."})
        plan = delta_marker.plan(data, [])
        self.assertEqual([n["ref"] for n in plan["create"]], ["$retry", "$swallow", "$clock"])
        self.assertEqual(plan["skipped"][0]["ref"], "$clock2")

    def test_decision_must_be_proposed(self) -> None:
        data = load("candidates.json")
        data["nodes"][0]["status"] = "active"
        with self.assertRaisesRegex(delta_marker.DeltaError, "proposed"):
            delta_marker.plan(data, [])

    def test_sources_must_be_real_and_cite_the_turn(self) -> None:
        for bad, message in (([], "at least one"), ([{"type": "url", "url": "TODO", "accessedAt": "2026-11-06"}], "placeholder"),
                             ([{"type": "repo", "path": "a.py", "extra": 1}], "unexpected keys"), ([{"type": "repo", "path": "a.py"}], "turn record")):
            data = load("candidates.json")
            data["nodes"][0]["sources"] = bad
            with self.assertRaisesRegex(delta_marker.DeltaError, message):
                delta_marker.plan(data, [])

    def test_marker_is_valid_for_the_stop_hook(self) -> None:
        plan = delta_marker.plan(load("candidates.json"), load("existing-nodes.json"))
        with tempfile.TemporaryDirectory() as tmp:
            refs = ["kn-acme-0031", "acme-retry-test-clock"] + plan["marker_hint"]
            path = delta_marker.write_marker(Path(tmp), "acme-42", refs)
            self.assertEqual(path, Path(tmp) / "deltas/acme-42.json")
            self.assertEqual(json.loads(path.read_text()), {"nodes": refs})
            self.assertEqual(stop.valid_delta(path), "")
            self.assertEqual(stop.delta_path(Path(tmp), "acme-42"), path)

    def test_marker_refuses_empty_local_refs_and_unsafe_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for agent, refs in (("acme-42", []), ("acme-42", ["  "]), ("acme-42", ["$retry"]), ("../x", ["kn-1"]), ("", ["kn-1"])):
                with self.assertRaises(delta_marker.DeltaError, msg=(agent, refs)):
                    delta_marker.write_marker(Path(tmp), agent, refs)
            self.assertFalse((Path(tmp) / "deltas").exists())

    def test_cli_plan_and_write(self) -> None:
        script = str(HARNESS / "scripts/delta_marker.py")
        done = subprocess.run([sys.executable, script, "plan", str(FIXTURES / "candidates.json"), str(FIXTURES / "existing-nodes.json")], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(json.loads(done.stdout)["create"]), 2)
        with tempfile.TemporaryDirectory() as tmp:
            env = {"PAI_HARNESS_STATE_DIR": tmp, "PATH": "/usr/bin:/bin"}
            ok = subprocess.run([sys.executable, script, "--config", str(FIXTURES / "acme.pai-harness.toml"), "write", "acme-42", "kn-acme-0031"], capture_output=True, text=True, env=env)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(stop.valid_delta(Path(tmp) / "deltas/acme-42.json"), "")
            bad = subprocess.run([sys.executable, script, "--config", str(FIXTURES / "acme.pai-harness.toml"), "write", "acme-42", "$retry"], capture_output=True, text=True, env=env)
            self.assertEqual(bad.returncode, 1)


class GateTriagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = harness_config.load_file(FIXTURES / "acme.pai-harness.toml")

    def test_failed_gate_names_owner_and_next_step(self) -> None:
        note = delta_marker.triage((FIXTURES / "failed-gate-output.txt").read_text(), self.config).splitlines()
        self.assertEqual([line.split(":")[0] for line in note], ["Done", "Next", "Blocked"])
        self.assertIn("E501", note[0])
        self.assertIn("acme-lead", note[1])
        self.assertIn("packages/contracts/schema/invoice.py", note[1])
        self.assertIn("re-run the gate", note[1])
        self.assertIn("ROOT", note[1])
        self.assertIn("frontend", note[2])

    def test_unowned_failure_goes_to_the_lead_not_a_guess(self) -> None:
        note = delta_marker.triage((FIXTURES / "failed-gate-unowned.txt").read_text(), self.config)
        self.assertIn("ask the lead to assign an owner", note)
        self.assertIn("owner unknown", note)

    def test_skill_tells_the_triager_to_use_zone_owners(self) -> None:
        text = (HARNESS / "skills/gate-triager/SKILL.md").read_text()
        for needle in ("[zones]", "owners", "Done:", "Next:", "Blocked:", "never edits code"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
