"""The stream renderer and the Herdr display: one readable line per event, workspace metadata with a TTL, the tab label."""
from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import SCRIPTS  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import render_stream as render  # noqa: E402

RENDER_FIXTURES = Path(__file__).resolve().parent / "fixtures/harness-render"
HOOKS = ("PreToolUse", "SessionStart", "Stop")


def stream(name: str) -> list[str]:
    return (RENDER_FIXTURES / f"{name}.jsonl").read_text().splitlines()


def rendered(name: str) -> list[str]:
    out = io.StringIO()
    renderer = render.Renderer(out, HOOKS)
    for line in stream(name):
        renderer.feed(line)
    return out.getvalue().splitlines()


class RendererTest(unittest.TestCase):
    def test_a_run_reads_as_one_line_per_event(self) -> None:
        lines = rendered("acme-run")
        self.assertEqual(lines[0], "▶ init model=claude-sonnet-5-5 skills=1 plugins=pai-harness hooks=PreToolUse,SessionStart,Stop")
        self.assertEqual(lines[2], "● tool Read apps/acme-storefront/src/checkout/totals.ts")
        self.assertEqual(lines[3], "● tool Edit apps/acme-storefront/src/checkout/totals.ts")
        self.assertTrue(lines[4].startswith("● tool Bash git log --oneline"))
        self.assertEqual(lines[5], "  ✗ tool error: fatal: not a git repository")
        self.assertEqual(lines[6], "  Totals fixed for ACME-7.")
        self.assertEqual(lines[-1], "■ result done turns=4 duration=12.4s cost≈$0.0421")
        self.assertEqual(len(lines), 8)  # tool results and the allowed rate-limit frame print nothing

    def test_long_text_and_commands_are_truncated_to_one_line(self) -> None:
        lines = rendered("acme-run")
        self.assertEqual(len(lines[1]), 2 + render.TEXT_LIMIT)
        self.assertTrue(lines[1].endswith("…"))
        self.assertLessEqual(len(lines[4]), len("● tool Bash ") + render.TOOL_LIMIT)
        self.assertTrue(lines[4].endswith("…"))
        self.assertTrue(all("\n" not in line for line in lines))

    def test_a_failed_and_a_blocked_result_say_so(self) -> None:
        self.assertEqual(rendered("acme-failed")[-1], "■ result failed turns=4 duration=9.0s cost≈$0.0300 (error_max_turns)")
        self.assertEqual(rendered("acme-blocked")[-1], "■ result blocked turns=3 duration=5.0s cost≈$0.0200 needs Bash")

    def test_a_line_that_is_not_json_is_shown_not_fatal(self) -> None:
        out = io.StringIO()
        renderer = render.Renderer(out)
        self.assertIsNone(renderer.feed("not json"))
        self.assertIsNone(renderer.feed("   "))
        self.assertIsNone(renderer.feed("[1]"))
        self.assertEqual(out.getvalue().splitlines(), ["? not json", "? [1]"])

    def test_a_rejected_rate_limit_is_shown_as_waiting(self) -> None:
        out = io.StringIO()
        frame = {"type": "rate_limit_event", "rate_limit_info": {"status": "rejected"}}
        render.Renderer(out).feed(json.dumps(frame))
        self.assertEqual(out.getvalue(), "… waiting: rate limited\n")
        self.assertEqual(render.frame_state(frame), "waiting")

    def test_the_filter_reads_stdin(self) -> None:
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("\n".join(stream("acme-run")))), mock.patch.object(sys, "stdout", out):
            self.assertEqual(render.main(), 0)
        self.assertIn("■ result done", out.getvalue())
        self.assertIn("hooks=PreToolUse,SessionStart,Stop", out.getvalue())  # read from this plugin's hooks.json


def run_status(name: str, final: str | None = None, workspace: str | None = "wAC", tab: str | None = "wAC:t3", returncode: int = 0) -> list[list[str]]:
    """Feed a fixture through a renderer and a HerdrStatus whose herdr calls are mocked; return every herdr argv."""
    calls: list[list[str]] = []

    def fake(argv, **kwargs):
        calls.append(argv[1:])
        self_timeout = kwargs.get("timeout")
        assert self_timeout, "a herdr call must have a timeout"
        return SimpleNamespace(returncode=returncode, stdout="", stderr="")

    renderer = render.Renderer(io.StringIO())
    status = render.HerdrStatus("ACME-7", "r1a2b3c4", workspace, tab, herdr="herdr")
    with mock.patch.object(render, "run_process", fake):
        for line in stream(name):
            frame = renderer.feed(line)
            if frame:
                status.observe(frame, renderer)
        if final:
            status.finish(final, renderer.step, renderer.turns)
    return calls


def without_seq(call: list[str]) -> list[str]:
    i = call.index("--seq")
    return call[:i] + call[i + 2:]


class HerdrStatusTest(unittest.TestCase):
    def metadata(self, calls: list[list[str]]) -> list[list[str]]:
        return [c for c in calls if c[:2] == ["workspace", "report-metadata"]]

    def test_every_event_reports_state_task_run_step_turns_and_a_ttl(self) -> None:
        calls = run_status("acme-run")
        meta = self.metadata(calls)
        self.assertEqual(len(meta), 11)  # one per frame of the fixture, tool results and the rate-limit frame included
        self.assertEqual(without_seq(meta[0]), ["workspace", "report-metadata", "wAC", "--source", "pai-harness", "--token", "state=working", "--token", "task=ACME-7",
                                                "--token", "run=r1a2b3c4", "--token", "step=-", "--token", "turns=0", "--ttl-ms", "120000"])
        edit = next(c for c in meta if "step=Edit apps/acme-storefront/src/checkout/totals.ts" in c)
        self.assertIn("turns=3", edit)
        self.assertIn("state=working", edit)
        last = without_seq(meta[-1])
        self.assertEqual((last[6], last[8], last[10]), ("state=done", "task=ACME-7", "run=r1a2b3c4"))
        self.assertTrue(last[12].startswith("step=Bash git log --oneline") and last[12].endswith("…"))
        self.assertEqual(last[14], "turns=4")
        self.assertTrue(all(c[c.index("--ttl-ms") + 1] == "120000" for c in meta))

    def test_the_sequence_only_goes_up(self) -> None:
        seqs = [int(c[c.index("--seq") + 1]) for c in self.metadata(run_status("acme-run", final="done"))]
        self.assertEqual(seqs, sorted(set(seqs)))

    def test_the_tab_label_follows_the_state_and_only_on_changes(self) -> None:
        renames = [c for c in run_status("acme-run") if c[:2] == ["tab", "rename"]]
        self.assertEqual(renames, [["tab", "rename", "wAC:t3", "ACME-7 · working"], ["tab", "rename", "wAC:t3", "ACME-7 · done"]])

    def test_a_failed_and_a_blocked_run_label_the_tab(self) -> None:
        for name, state in (("acme-failed", "failed"), ("acme-blocked", "blocked")):
            renames = [c[3] for c in run_status(name) if c[:2] == ["tab", "rename"]]
            self.assertEqual(renames, ["ACME-7 · working", f"ACME-7 · {state}"])

    def test_the_record_state_overrides_a_success_frame_and_the_tokens_are_cleared_last(self) -> None:
        calls = run_status("acme-run", final="failed")  # the exit code failed a run whose result frame said success
        self.assertEqual(calls[-2][:2], ["tab", "rename"])
        self.assertEqual(calls[-2][3], "ACME-7 · failed")
        clear = without_seq(calls[-1])
        self.assertEqual(clear, ["workspace", "report-metadata", "wAC", "--source", "pai-harness", "--clear-token", "state", "--clear-token", "task",
                                 "--clear-token", "run", "--clear-token", "step", "--clear-token", "turns"])
        self.assertNotIn("--ttl-ms", clear)

    def test_clearing_after_a_final_frame_does_not_repeat_the_state(self) -> None:
        calls = self.metadata(run_status("acme-run", final="done"))
        self.assertEqual(len(calls), 12)  # 11 events, then the clear: the final state was already shown by the result frame
        self.assertIn("--clear-token", calls[-1])

    def test_no_workspace_or_tab_means_no_calls(self) -> None:
        self.assertEqual(run_status("acme-run", workspace=None, tab=None, final="done"), [])
        self.assertEqual([c[:2] for c in run_status("acme-run", workspace=None)], [["tab", "rename"], ["tab", "rename"]])

    def test_a_herdr_that_keeps_failing_goes_quiet_and_never_raises(self) -> None:
        calls = run_status("acme-run", final="done", returncode=1)
        self.assertEqual(len(calls), 3)

    def test_a_missing_herdr_binary_is_not_an_error(self) -> None:
        status = render.HerdrStatus("ACME-7", "r1", "wAC", "wAC:t3", herdr="/nonexistent/herdr")
        status.report("working", "", 0)
        status.finish("done", "", 0)
        self.assertFalse(status.active)


if __name__ == "__main__":
    unittest.main()
