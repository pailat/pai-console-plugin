"""Stop zone diff base (ATE-1203): the launch commit, [project] base_branch, and the capped block text."""
from __future__ import annotations

import subprocess
from pathlib import Path

from tests.test_harness_zone_diff import ZoneDiffCase

IDENT = ("-c", "user.name=Acme", "-c", "user.email=acme@example.com")


class ReleaseBranchCase(ZoneDiffCase):
    """main holds the base commit; a release branch carries unrelated work, and the agent's worktree branches off the release."""

    def setUp(self) -> None:
        super().setUp()
        self.git("checkout", "-q", "-b", "release")
        for n in range(15):
            self.write(f"packages/contracts/release-{n}.ts", "release\n")
        self.git("add", "-A")
        self.git(*IDENT, "commit", "-q", "-m", "release work")
        self.git("checkout", "-q", "-b", "agent")
        self.start = subprocess.run(["git", "-C", str(self.project), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


class LaunchBaseTest(ReleaseBranchCase):
    def set_config(self, line: str) -> None:
        """Add a [project] line on the release branch and move the agent branch there, so the config edit itself is not a changed path."""
        self.git("checkout", "-q", "release")
        config = self.project / ".pai-harness.toml"
        config.write_text(config.read_text().replace("[project]\n", f"[project]\n{line}\n", 1))
        self.git("add", "-A")
        self.git(*IDENT, "commit", "-q", "-m", "config")
        self.git("checkout", "-q", "agent")
        self.git("reset", "-q", "--hard", "release")
        self.start = subprocess.run(["git", "-C", str(self.project), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()

    def test_without_a_base_the_release_files_are_flagged_against_main(self) -> None:
        result = self.stop()
        self.assertEqual(result["decision"], "block")
        self.assertIn("release-0.ts", result["reason"])

    def test_the_launch_base_ignores_unrelated_release_files(self) -> None:
        self.assertIsNone(self.stop(PAI_HARNESS_BASE=self.start))

    def test_the_launch_base_still_flags_the_agents_own_out_of_zone_commit(self) -> None:
        self.write("packages/contracts/mine.ts", "x\n")
        self.git("add", "-A")
        self.git(*IDENT, "commit", "-q", "-m", "mine")
        result = self.stop(PAI_HARNESS_BASE=self.start)
        self.assertBlocked(result, "packages/contracts/mine.ts")
        self.assertNotIn("release-0.ts", result["reason"])

    def test_base_branch_in_the_config_is_the_fallback_before_main(self) -> None:
        self.set_config('base_branch = "release"')
        self.assertIsNone(self.stop())

    def test_the_launch_base_wins_over_base_branch(self) -> None:
        self.set_config('base_branch = "main"')
        self.assertIsNone(self.stop(PAI_HARNESS_BASE=self.start))

    def test_an_unknown_base_branch_falls_through_to_the_candidates(self) -> None:
        self.set_config('base_branch = "nope"')
        self.assertIn("release-0.ts", self.stop()["reason"])


class CappedBlockTest(ZoneDiffCase):
    def test_the_block_lists_ten_paths_and_the_total(self) -> None:
        for n in range(25):
            self.write(f"packages/contracts/f{n:02d}.ts", "x\n")
        result = self.stop()
        reason = result["reason"]
        self.assertEqual(reason.count("Write zone:"), 10)
        self.assertIn("25 paths in all", reason)
        self.assertIn("... and 15 more", reason)

    def test_a_short_list_is_shown_whole(self) -> None:
        for n in range(3):
            self.write(f"packages/contracts/f{n}.ts", "x\n")
        reason = self.stop()["reason"]
        self.assertEqual(reason.count("Write zone:"), 3)
        self.assertNotIn("paths in all", reason)
        self.assertNotIn("more", reason)
