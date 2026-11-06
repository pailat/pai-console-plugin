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
        self.assertEqual(self.verdict("scripts/queue-push.sh origin staging", {"PAI_HARNESS_PROTECTED_BRANCHES": ""}), "")


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
