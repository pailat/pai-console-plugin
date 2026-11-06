"""cost_report: per-day, per-role and per-model totals from the run records; unpriced runs are not counted as free."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import HarnessCase  # noqa: E402


class CostReportTest(HarnessCase):
    def write(self, issue: str, **fields: object) -> None:
        runs = self.state / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        (runs / f"{issue}.state.json").write_text(json.dumps({"issue": issue, "state": "done", "turns": 10, **fields}))

    def test_totals_by_role_and_model_for_one_day(self) -> None:
        self.write("ACME-1", finished="2026-11-06T10:00:00Z", role="implementer", model="sonnet", cost_usd=1.5, peak_context_tokens=90000)
        self.write("ACME-2", finished="2026-11-06T11:00:00Z", role="implementer", model="sonnet", cost_usd=0.5)
        self.write("ACME-3", finished="2026-11-06T12:00:00Z", role="mechanical", model="haiku", cost_usd=None, state="failed")
        self.write("ACME-4", finished="2026-11-05T12:00:00Z", role="implementer", model="sonnet", cost_usd=9.0)
        done = self.run_script("cost_report.sh", "--day", "2026-11-06", "--merged", "2", "--json")
        self.assertEqual(done.returncode, 0, done.stderr)
        report = json.loads(done.stdout)
        self.assertEqual(report["by_role"]["implementer"]["cost_usd"], 2.0)
        self.assertEqual(report["by_role"]["implementer"]["peak_context_tokens"], 90000)
        self.assertEqual((report["by_role"]["mechanical"]["unpriced"], report["by_role"]["mechanical"]["failed"]), (1, 1))
        self.assertEqual(report["total"]["runs"], 3)
        self.assertEqual(report["cost_per_merged_pr_usd"], 1.0)


    def test_the_total_line_shows_unpriced_runs_and_flags_the_per_pr_cost_as_a_lower_bound(self) -> None:
        self.write("ACME-1", finished="2026-11-06T10:00:00Z", role="implementer", model="sonnet", cost_usd=1.0)
        self.write("ACME-2", finished="2026-11-06T11:00:00Z", role="implementer", model="sonnet", cost_usd=None, state="failed")
        done = self.run_script("cost_report.sh", "--day", "2026-11-06", "--merged", "1")
        self.assertIn("total usd=1.00 runs=2 unpriced=1 per_merged_pr=>=1.0", done.stdout)
        report = json.loads(self.run_script("cost_report.sh", "--day", "2026-11-06", "--merged", "1", "--json").stdout)
        self.assertTrue(report["cost_per_merged_pr_lower_bound"])

    def test_a_bad_day_or_a_non_positive_merged_count_is_refused(self) -> None:
        for argv in (("--day", "2026-11-6"), ("--day", "yesterday"), ("--merged", "-3"), ("--merged", "0"), ("--merged", "x")):
            done = self.run_script("cost_report.sh", *argv)
            self.assertEqual(done.returncode, 2, argv)
            self.assertTrue(done.stderr.strip(), argv)


if __name__ == "__main__":
    unittest.main()
