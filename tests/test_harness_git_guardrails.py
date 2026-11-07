"""Fixture tests of the git-guardrails hook: Acme commands only, real hook JSON on stdin."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "plugins/pai-harness/hooks"
FIXTURES = Path(__file__).resolve().parent / "fixtures/harness-hooks"
CASES = json.loads((FIXTURES / "git-guardrails-cases.json").read_text())
WRAPPER = "scripts/queue-push.sh"
sys.path.insert(0, str(HOOKS))
import git_guardrails  # noqa: E402


class GuardrailTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name).resolve() / "acme-wt"
        (self.project / "scratch/sub").mkdir(parents=True)
        (self.project / "apps").mkdir()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        (self.project / "sub").mkdir()
        (self.project / ".pai-harness.toml").write_text((FIXTURES / "acme.pai-harness.toml").read_text())
        self.home = Path(self._tmp.name) / "home"
        self.home.mkdir()
        self.env = {"PATH": os.environ["PATH"], "HOME": str(self.home), "GIT_CONFIG_NOSYSTEM": "1", "PAI_HARNESS_ROLE": "implementer",
                    "PAI_HARNESS_AGENT": "acme-7", "PAI_HARNESS_ZONES": "frontend", "PAI_HARNESS_PUSH_WRAPPER": WRAPPER,
                    "PAI_HARNESS_STATE_DIR": str(Path(self._tmp.name) / "state")}

    def verdict(self, command: str, env: dict | None = None, cwd: str = ".") -> str:
        old = {k: os.environ.get(k) for k in (env or {})}
        os.environ.update(env or {})
        try:
            reason = git_guardrails.check(command, WRAPPER, (self.project / cwd).resolve())
            if not reason and "push" in command:  # a direct push is refused whole by the older push guard, not by the module
                out = self.hook(command, "bypassPermissions", (self.project / cwd).resolve())
                reason = out["hookSpecificOutput"]["permissionDecisionReason"] if out else ""
            return reason
        finally:
            for key, value in old.items():
                os.environ.pop(key, None) if value is None else os.environ.__setitem__(key, value)

    def hook(self, command: str, mode: str, cwd: Path | None = None) -> dict | None:
        event = {"session_id": "sess-1", "cwd": str(cwd or self.project), "permission_mode": mode, "hook_event_name": "PreToolUse",
                 "tool_name": "Bash", "tool_use_id": "toolu_1", "tool_input": {"command": command}}
        done = subprocess.run([sys.executable, str(HOOKS / "pre_tool_use.py")], input=json.dumps(event), text=True, capture_output=True,
                              env={**self.env, **{k: v for k, v in os.environ.items() if k.startswith(("PAI_HARNESS_GIT", "PAI_HARNESS_PROTECTED"))}}, cwd=self.project, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout) if done.stdout.strip() else None


class Item9TableTest(GuardrailTest):
    """Every command of the plugin-verify item 9 table, through the real hook, in default and in bypass-permissions mode."""

    def test_blocked_commands_are_denied_in_every_permission_mode(self) -> None:
        for mode in ("default", "acceptEdits", "bypassPermissions"):
            for command in CASES["table"]["deny"]:
                with self.subTest(mode=mode, command=command):
                    out = self.hook(command, mode)
                    self.assertIsNotNone(out)
                    decision = out["hookSpecificOutput"]
                    self.assertEqual(decision["permissionDecision"], "deny")
                    if not command.startswith("git push"):  # a direct push is refused by the older push guard
                        self.assertIn("git-guardrails", decision["permissionDecisionReason"])
                        self.assertIn("Safe alternative", decision["permissionDecisionReason"])

    def test_a_block_names_the_command(self) -> None:
        out = self.hook("git reset --hard HEAD~1", "bypassPermissions")
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("`git reset --hard HEAD~1`", reason)

    def test_allowed_commands_pass_in_every_permission_mode(self) -> None:
        for mode in ("default", "bypassPermissions"):
            for command in CASES["table"]["allow"]:
                with self.subTest(mode=mode, command=command):
                    self.assertIsNone(self.hook(command, mode))

    def test_no_role_means_the_hook_is_inert(self) -> None:
        self.env["PAI_HARNESS_ROLE"] = ""
        self.assertIsNone(self.hook("git reset --hard", "default"))


class SyntaxTest(GuardrailTest):
    def test_no_syntax_hides_a_dangerous_command(self) -> None:
        for command in CASES["syntax"]["deny"]:
            with self.subTest(command=command):
                self.assertTrue(self.verdict(command), "not blocked")

    def test_harmless_commands_are_not_blocked(self) -> None:
        for command in CASES["syntax"]["allow"]:
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command), "")

    def test_a_repository_alias_is_read(self) -> None:
        subprocess.run(["git", "-C", str(self.project), "config", "alias.nuke", "reset --hard"], check=True)
        subprocess.run(["git", "-C", str(self.project), "config", "alias.sh", "!git clean -fd"], check=True)
        subprocess.run(["git", "-C", str(self.project), "config", "alias.ok", "status"], check=True)
        self.assertTrue(self.verdict("git nuke"))
        self.assertTrue(self.verdict("git sh"))
        self.assertEqual(self.verdict("git ok"), "")


class NoGoRoundTest(GuardrailTest):
    """ROOT NO-GO on PR 49: shell flag clusters, xargs, substitutions, other shells, env -S, same-command aliases."""

    def test_every_repro_row_is_denied_in_every_permission_mode(self) -> None:
        for mode in ("default", "acceptEdits", "bypassPermissions"):
            for command in CASES["nogo"]["deny"]:
                with self.subTest(mode=mode, command=command):
                    out = self.hook(command, mode)
                    self.assertIsNotNone(out, "not blocked")
                    self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_the_controls_still_pass_in_every_permission_mode(self) -> None:
        for mode in ("default", "bypassPermissions"):
            for command in CASES["nogo"]["allow"]:
                with self.subTest(mode=mode, command=command):
                    self.assertIsNone(self.hook(command, mode))

    def test_the_older_guard_reads_the_same_shell_clusters(self) -> None:
        for command in ("bash -ce 'git push origin HEAD'", "sh -c -e 'git push origin HEAD'", "bash -c -- 'git push origin HEAD'"):
            with self.subTest(command=command):
                self.assertEqual(self.hook(command, "bypassPermissions")["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_a_substitution_is_read_as_its_own_command(self) -> None:
        self.assertTrue(self.verdict("echo $(git reset --hard)"))
        self.assertTrue(self.verdict("echo \"$(git clean -fd)\""))
        self.assertEqual(self.verdict("echo '$(git reset --hard)'"), "")


class ProtectedBranchTest(GuardrailTest):
    def test_head_is_resolved_to_the_current_branch(self) -> None:
        git = ["git", "-C", str(self.project)]
        subprocess.run([*git, "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        self.assertTrue(self.verdict("scripts/queue-push.sh origin HEAD"))
        self.assertTrue(self.verdict("scripts/queue-push.sh origin"))
        subprocess.run([*git, "symbolic-ref", "HEAD", "refs/heads/feat/acme-7"], check=True)
        self.assertEqual(self.verdict("scripts/queue-push.sh origin HEAD"), "")
        self.assertTrue(self.verdict("scripts/queue-push.sh origin HEAD:main"))


class WrapperFormsTest(GuardrailTest):
    """The wrapper is called as `wrapper git push ...` as well as `wrapper REMOTE REFSPEC`; a bare HEAD, `@`, a glob or --all all reach main."""

    def on(self, branch: str) -> None:
        subprocess.run(["git", "-C", str(self.project), "symbolic-ref", "HEAD", f"refs/heads/{branch}"], check=True)

    def test_the_git_push_form_is_read_like_the_short_form(self) -> None:
        self.on("main")
        for command in ("scripts/queue-push.sh git push", "scripts/queue-push.sh git push origin", "scripts/queue-push.sh git push -u origin",
                        "scripts/queue-push.sh git push --all origin", "scripts/queue-push.sh origin @", "scripts/queue-push.sh git -C . push origin HEAD"):
            with self.subTest(command=command):
                self.assertTrue(self.verdict(command), "not blocked")
        self.on("feat/acme-7")
        for command in ("scripts/queue-push.sh git push", "scripts/queue-push.sh git push -u origin HEAD", "scripts/queue-push.sh origin @", "scripts/queue-push.sh git status"):
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command), "")

    def test_cd_changes_the_directory_a_bare_head_is_read_in(self) -> None:
        other = self.project.parent / "main-checkout"
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        subprocess.run(["git", "-C", str(other), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        self.on("feat/acme-7")
        self.assertTrue(self.verdict(f"cd {other} && scripts/queue-push.sh origin HEAD"))
        self.assertTrue(self.verdict(f"pushd {other}; scripts/queue-push.sh git push"))
        self.assertTrue(self.verdict(f"scripts/queue-push.sh git -C {other} push origin HEAD"))
        self.assertTrue(self.verdict("cd $WHERE && scripts/queue-push.sh origin HEAD"))  # not static: refused
        self.assertTrue(self.verdict(f"cd {other}/missing && scripts/queue-push.sh origin HEAD"))  # not a directory: refused
        self.assertEqual(self.verdict(f"cd {other} && scripts/queue-push.sh origin feat/acme-7"), "")
        self.on("main")
        self.assertTrue(self.verdict(f"(cd {self.project.parent} ; true); scripts/queue-push.sh origin HEAD"))  # the session directory is read too

    def test_a_git_timeout_denies_and_is_not_repeated(self) -> None:
        self.on("feat/acme-7")
        calls = []

        def slow(command, **kwargs):
            calls.append(command)
            raise subprocess.TimeoutExpired(command, 3)

        original, git_guardrails.run_process = git_guardrails.run_process, slow
        try:
            reason = git_guardrails.check("scripts/queue-push.sh origin HEAD; scripts/queue-push.sh origin HEAD", WRAPPER, self.project)
            self.assertIn("could not be read in time", reason)
            self.assertEqual(len(calls), 1, "the failed lookup is cached for the rest of the check")
            self.assertIn("could not be read in time", git_guardrails.check("git status", WRAPPER, self.project))
            self.assertEqual(git_guardrails.check("scripts/queue-push.sh origin feat/acme-7", WRAPPER, self.project), "")
        finally:
            git_guardrails.run_process = original

    def test_a_lookup_is_made_once_per_directory(self) -> None:
        self.on("feat/acme-7")
        calls = []
        original = git_guardrails.run_process
        git_guardrails.run_process = lambda command, **kwargs: (calls.append(command), original(command, **kwargs))[1]
        try:
            self.assertEqual(git_guardrails.check("; ".join(["scripts/queue-push.sh origin HEAD"] * 4), WRAPPER, self.project), "")
        finally:
            git_guardrails.run_process = original
        self.assertEqual(len(calls), 1)

    def test_no_verify_is_left_to_the_older_guard_in_any_case(self) -> None:
        self.on("feat/acme-7")
        for command in ("scripts/queue-push.sh git -c core.hookspath=/dev/null push origin feat/acme-7", "scripts/queue-push.sh --no-verif origin feat/acme-7"):
            with self.subTest(command=command):
                self.assertEqual(git_guardrails.check(command, WRAPPER, self.project), "")
                out = self.hook(command, "bypassPermissions")
                self.assertIn("--no-verify", out["hookSpecificOutput"]["permissionDecisionReason"])


class ProtectedListTest(GuardrailTest):
    def test_the_list_is_replaced_by_the_environment(self) -> None:
        self.assertTrue(self.verdict("scripts/queue-push.sh origin main"))
        only = {"PAI_HARNESS_PROTECTED_BRANCHES": "develop,trunk,hotfix/*"}
        self.assertTrue(self.verdict("scripts/queue-push.sh origin develop", only))
        self.assertTrue(self.verdict("scripts/queue-push.sh origin HEAD:hotfix/1", only))
        self.assertEqual(self.verdict("scripts/queue-push.sh origin main", only), "")
        for empty in ("", ",", " : "):  # an empty or separator-only value keeps the default list; it never disables protection
            self.assertTrue(self.verdict("scripts/queue-push.sh origin staging", {"PAI_HARNESS_PROTECTED_BRANCHES": empty}))


class DeltaRoundTest(GuardrailTest):
    """Second review round: crashes and fail-open inputs first, then over-denial."""

    def on(self, branch: str) -> None:
        subprocess.run(["git", "-C", str(self.project), "symbolic-ref", "HEAD", f"refs/heads/{branch}"], check=True)

    def test_an_unparseable_wrapper_never_crashes_the_hook(self) -> None:
        self.assertEqual(git_guardrails.check("git status", "scripts/q 'x", self.project), "")
        self.env["PAI_HARNESS_PUSH_WRAPPER"] = "scripts/q 'x"
        self.hook("git push origin main", "bypassPermissions")  # hook() asserts a zero exit status
        self.hook("scripts/q origin main", "default")

    def test_git_dir_and_work_tree_do_not_crash_the_guard(self) -> None:
        for command in ("git --git-dir=.git status", "git --git-dir .git status", "git --work-tree=. status", "git --git-dir=.git config user.name x"):
            with self.subTest(command=command):
                self.assertEqual(git_guardrails.check(command, WRAPPER, self.project), "")
        for command in ("git --git-dir=.git reset --hard", "git --work-tree=. clean -fd",
                        "git --git-dir=.git checkout .", "git --git-dir=.git branch -D x"):
            with self.subTest(command=command):
                self.assertTrue(git_guardrails.check(command, WRAPPER, self.project), "not blocked")
        for command in ("git --git-dir=.git reset --hard", "git --git-dir=.git push --force origin main", "scripts/queue-push.sh git --git-dir=.git push -f origin x"):
            out = self.hook(command, "bypassPermissions")  # hook() asserts a zero exit status
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny", command)

    def test_a_parser_crash_denies_through_the_real_hook(self) -> None:
        sentinel = self.project / "boom.py"
        sentinel.write_text("import sys; sys.path.insert(0, %r)\nimport git_guardrails as g\ng.segments = lambda c: 1 / 0\nimport pre_tool_use as p; p.main()\n" % str(HOOKS))
        event = {"session_id": "s", "cwd": str(self.project), "permission_mode": "bypassPermissions", "hook_event_name": "PreToolUse",
                 "tool_name": "Bash", "tool_use_id": "t", "tool_input": {"command": "git status"}}
        done = subprocess.run([sys.executable, str(sentinel)], input=json.dumps(event), text=True, capture_output=True, env=self.env, cwd=self.project, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("could not be checked", json.loads(done.stdout)["hookSpecificOutput"]["permissionDecisionReason"])

    def test_an_internal_error_denies(self) -> None:
        class Common:
            reasons: list = []

            @staticmethod
            def deny(reason: str) -> None:
                Common.reasons.append(reason)

        original, git_guardrails.check = git_guardrails.check, lambda *a: 1 / 0
        try:
            self.assertTrue(git_guardrails.deny_dangerous(Common, "git status", WRAPPER, self.project))
        finally:
            git_guardrails.check = original
        self.assertIn("could not be checked", Common.reasons[0])

    def test_any_spelling_of_the_wrapper_path_is_the_wrapper(self) -> None:
        for spelling in ("./scripts/queue-push.sh", str(self.project / "scripts/queue-push.sh"), "scripts/../scripts/queue-push.sh"):
            for tail in ("origin main", "--all origin", "-f origin x"):
                with self.subTest(spelling=spelling, tail=tail):
                    self.assertTrue(self.verdict(f"{spelling} {tail}"), "not blocked")
        self.assertEqual(self.verdict("./scripts/queue-push.sh origin feat/acme-7"), "")
        out = self.hook("./scripts/queue-push.sh git push origin feat/acme-7", "default")
        self.assertIsNone(out)  # a wrapper push is not a direct push, whatever its spelling
        self.assertIsNotNone(self.hook("./scripts/queue-push.sh --no-verify origin feat/acme-7", "default"))

    def test_a_shell_with_combined_flags_does_not_hide_a_push(self) -> None:
        for command in ("bash -lc 'git push --force origin main'", "bash -ec 'git push origin main'", "sudo -u x bash -lc 'git push origin main'",
                        "bash -lc 'scripts/queue-push.sh --no-verify origin x'", "bash -lc 'scripts/queue-push.sh origin main'"):
            with self.subTest(command=command):
                out = self.hook(command, "bypassPermissions")
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_a_refspec_built_at_run_time_is_refused(self) -> None:
        self.on("feat/acme-7")
        for tail in ("origin $B", "origin ${B}", "origin $(echo main)", "origin `echo main`", "origin HEAD:$B", "origin ~", "origin feat:heads/main",
                     "origin feat:refs/heads/main", "origin \"$(git branch --show-current)\""):
            with self.subTest(tail=tail):
                self.assertTrue(self.verdict(f"scripts/queue-push.sh {tail}"), "not blocked")
        self.assertEqual(self.verdict("scripts/queue-push.sh origin feat/acme-7"), "")

    def test_an_unknown_cwd_is_not_rescued_by_a_relative_dash_c(self) -> None:
        self.on("feat/acme-7")
        (self.project / "sub").mkdir(exist_ok=True)
        self.assertTrue(self.verdict("cd $X && scripts/queue-push.sh git -C sub push origin HEAD"))
        self.assertEqual(self.verdict("scripts/queue-push.sh git -C sub push origin feat/acme-7"), "")

    def test_a_detached_head_names_no_branch(self) -> None:
        git = ["git", "-C", str(self.project), "-c", "user.name=Acme", "-c", "user.email=a@acme.test"]
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        subprocess.run([*git, "checkout", "-q", "--detach"], check=True)
        self.assertIn("detached", self.verdict("scripts/queue-push.sh origin HEAD"))
        self.assertEqual(self.verdict("scripts/queue-push.sh origin feat/acme-7"), "")

    def test_a_missing_directory_is_not_blamed_on_a_timeout(self) -> None:
        self.on("feat/acme-7")
        self.assertEqual(self.verdict("git -C /nonexistent-acme status"), "")
        self.assertEqual(self.verdict("git clone https://acme.test/y.git y && cd y && git status"), "")
        self.assertEqual(self.verdict("mkdir d && git -C d init"), "")
        reason = self.verdict("cd y && scripts/queue-push.sh origin HEAD")
        self.assertIn("does not exist", reason)

    def test_rm_of_an_ordinary_glob_is_allowed_but_a_dot_glob_is_not(self) -> None:
        for command in ("rm -rf dist/*", "rm -rf node_modules/*", "rm -rf build/[a-z]*"):
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command), "")
        for command in ("rm -rf .*", "rm -rf .g*", "rm -rf .[g]it", "rm -rf [.]git"):
            with self.subTest(command=command):
                self.assertTrue(self.verdict(command), "not blocked")

    def test_the_pipe_scan_only_fires_for_a_shell_that_a_pipe_feeds(self) -> None:
        self.on("feat/acme-7")
        for command in ("bash run.sh && git restore --staged foo", "bash run.sh && scripts/queue-push.sh origin feat/acme-7"):
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command), "")
        self.assertEqual(git_guardrails.check("bash scripts/queue-push.sh origin feat/acme-7", "bash scripts/queue-push.sh", self.project), "")
        self.assertTrue(git_guardrails.check("echo hi | bash scripts/queue-push.sh origin main", "bash scripts/queue-push.sh", self.project))
        self.assertTrue(self.verdict("echo 'git reset --hard' | sh"))

    def test_commands_with_the_same_effect_as_blocked_ones_are_blocked(self) -> None:
        for command in ("git switch -f x", "git switch --discard-changes x", "git switch -C x", "git checkout -B x", "git filter-branch --all",
                        "git reflog expire --expire=now --all", "git reflog delete HEAD@{1}", "git gc --prune=now", "git tag -d v1", "git remote rm origin"):
            with self.subTest(command=command):
                self.assertTrue(self.verdict(command), "not blocked")
        for command in ("git switch -c x", "git switch x", "git gc", "git tag v1", "git reflog", "git remote -v", "git fetch --prune", "git reset --merge"):
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command), "")


class FailClosedTest(GuardrailTest):
    """Anything the reader cannot resolve to literal words is refused, with a reason that names it."""

    def reasons(self, command: str) -> str:
        return git_guardrails.check(command, WRAPPER, self.project)

    def test_the_reason_names_what_could_not_be_resolved(self) -> None:
        for command, named in (("git reset $(echo --hard)", "substitution"), ("git reset $X", "variable"), ("git $'reset' --hard", "ANSI-C"),
                               ("echo 'git reset --hard' | bash", "script fed by a pipe"), ("git reset --hard \"x", "unmatched quote"),
                               ("git " + "a " * 40000, "too large"), ("; ".join(["true"] * 2500), "too large"), ("bash -c \"$cmd\"", "built by a variable"),
                               ("echo x | xargs git reset", "xargs feeds"), ("GIT_CONFIG_COUNT=1 git status", "GIT_CONFIG_*")):
            with self.subTest(command=command[:40]):
                self.assertIn(named, self.reasons(command))

    def test_the_overall_deadline_denies_with_the_segment_count(self) -> None:
        original, git_guardrails.PARSE_BUDGET = git_guardrails.PARSE_BUDGET, -1
        try:
            reason = "; ".join(["git status"] * 50)
            hook_reason = None
            with self.assertRaises(TimeoutError):
                git_guardrails.check(reason, WRAPPER, self.project)
            class Common:
                reasons: list = []
                deny = staticmethod(lambda text: Common.reasons.append(text))
            self.assertTrue(git_guardrails.deny_dangerous(Common, reason, WRAPPER, self.project))
            self.assertIn("deadline exceeded after 1 segments", Common.reasons[0])
        finally:
            git_guardrails.PARSE_BUDGET = original

    def test_large_input_is_answered_well_inside_the_hook_timeout(self) -> None:
        import time
        for command in ("git " + "a " * 30000, "; ".join(["git status"] * 1900), "x" * 60000 + " git status"):
            started = time.monotonic()
            self.hook(command, "bypassPermissions")
            self.assertLess(time.monotonic() - started, 8, command[:30])

    def test_a_crash_in_analyze_denies_through_the_real_hook(self) -> None:
        boom = self.project / "boom2.py"
        boom.write_text("import sys; sys.path.insert(0, %r)\nimport pre_tool_use as p\np.analyze = lambda *a, **k: 1 / 0\np.main()\n" % str(HOOKS))
        event = {"session_id": "s", "cwd": str(self.project), "permission_mode": "bypassPermissions", "hook_event_name": "PreToolUse",
                 "tool_name": "Bash", "tool_use_id": "t", "tool_input": {"command": "git status"}}
        done = subprocess.run([sys.executable, str(boom)], input=json.dumps(event), text=True, capture_output=True, env=self.env, cwd=self.project, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("could not check this call", json.loads(done.stdout)["hookSpecificOutput"]["permissionDecisionReason"])
        self.env["PAI_HARNESS_ROLE"] = ""
        done = subprocess.run([sys.executable, str(boom)], input=json.dumps(event), text=True, capture_output=True, env=self.env, cwd=self.project, timeout=60)
        self.assertEqual(done.stdout.strip(), "")  # no role: the hook stays inert


class ThrowawayTest(GuardrailTest):
    def test_denied_without_a_valid_opt_in(self) -> None:
        for case in CASES["throwaway"]["deny"]:
            with self.subTest(case=case):
                self.assertTrue(self.verdict(case["command"], case["env"], case.get("cwd", ".")), "not blocked")

    def test_allowed_inside_an_opted_in_throwaway_path(self) -> None:
        for case in CASES["throwaway"]["allow"]:
            with self.subTest(case=case):
                self.assertEqual(self.verdict(case["command"], case["env"], case.get("cwd", ".")), "")


if __name__ == "__main__":
    unittest.main()
