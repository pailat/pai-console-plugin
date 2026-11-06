"""Fixture tests of the pai-harness hooks: real hook JSON on stdin, exact decision output on stdout."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "plugins/pai-harness/hooks"
FIXTURES = Path(__file__).resolve().parent / "fixtures/harness-hooks"
WRAPPER = "queue-push.sh"


def deny(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}


class HookCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name).resolve() / "project"
        self.project.mkdir()
        shutil.copy(FIXTURES / "acme.pai-harness.toml", self.project / ".pai-harness.toml")
        self.state = Path(self._tmp.name).resolve() / "state"
        self.env = {"PATH": os.environ["PATH"], "HOME": self._tmp.name, "PAI_HARNESS_ROLE": "implementer", "PAI_HARNESS_AGENT": "acme-7",
                    "PAI_HARNESS_ZONES": "frontend", "PAI_HARNESS_STATE_DIR": str(self.state), "PAI_HARNESS_PUSH_WRAPPER": WRAPPER}

    def event(self, name: str) -> str:
        text = (FIXTURES / f"{name}.json").read_text()
        for key, value in (("__PROJECT__", str(self.project)), ("__WORKTREE__", str(getattr(self, "worktree", self.project))), ("__STATE__", str(self.state)), ("__WRAPPER__", WRAPPER)):
            text = text.replace(key, value)
        json.loads(text)
        return text

    def run_hook(self, script: str, name: str, **env: str | None) -> dict | None:
        merged = {**self.env, **env}
        merged = {k: v for k, v in merged.items() if v is not None}
        done = subprocess.run([sys.executable, str(HOOKS / script)], input=self.event(name), text=True, capture_output=True, env=merged,
                              cwd=self.project, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout) if done.stdout.strip() else None

    def pre(self, name: str, **env: str | None) -> dict | None:
        return self.run_hook("pre_tool_use.py", name, **env)


class HooksManifestTest(unittest.TestCase):
    def test_every_event_runs_its_script(self) -> None:
        hooks = json.loads((HOOKS / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "Stop", "PreToolUse"})
        for event, script in (("SessionStart", "session_start.py"), ("Stop", "stop.py"), ("PreToolUse", "pre_tool_use.py")):
            self.assertEqual(hooks[event][0]["hooks"][0]["command"], f'python3 "${{CLAUDE_PLUGIN_ROOT}}/hooks/{script}"')
            self.assertTrue((HOOKS / script).is_file())
        self.assertEqual(hooks["PreToolUse"][0]["matcher"], "Write|Edit|MultiEdit|NotebookEdit|Bash")

    def test_no_hook_uses_the_ask_decision(self) -> None:
        for path in HOOKS.glob("*.py"):
            self.assertNotIn('"ask"', path.read_text(), path.name)


class SessionStartTest(HookCase):
    def test_injects_the_brief_and_the_knowledge(self) -> None:
        brief = Path(self._tmp.name) / "brief.md"
        brief.write_text("Implement ACME-7 for the Acme app.\n")
        knowledge = Path(self._tmp.name) / "knowledge.py"
        knowledge.write_text("import json, sys\nrequest = json.load(sys.stdin)\nprint('- DEC-1 Acme uses CAS (' + request['role'] + ', ' + request['project']['pai_project'] + ')')\n")
        out = self.run_hook("session_start.py", "session-start", PAI_HARNESS_BRIEF=str(brief), PAI_HARNESS_KNOWLEDGE_CMD=f"{sys.executable} {knowledge}")
        self.assertEqual(out, {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": (
            "# Pai Harness session (implementer)\n\n## Brief\n\nImplement ACME-7 for the Acme app.\n\n"
            "## Curated Knowledge\n\n- DEC-1 Acme uses CAS (implementer, acme-app)")}})

    def test_says_so_when_the_brief_or_knowledge_is_missing(self) -> None:
        out = self.run_hook("session_start.py", "session-start", PAI_HARNESS_BRIEF=str(self.project / "missing.md"), PAI_HARNESS_KNOWLEDGE_CMD="false")
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("could not be read", context)
        self.assertIn("The Knowledge fetch returned nothing", context)

    def test_without_a_role_it_does_nothing(self) -> None:
        self.assertIsNone(self.run_hook("session_start.py", "session-start", PAI_HARNESS_ROLE=None, PAI_HARNESS_BRIEF="x"))


class StopTest(HookCase):
    def deltas(self, name: str) -> Path:
        return self.state / "deltas" / name

    def marker(self, data: object) -> Path:
        path = self.state / "deltas" / "acme-7.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data))
        return path

    def blocked(self, problem: str) -> dict:
        path = self.state / "deltas" / "acme-7.json"
        return {"decision": "block", "reason": (
            f"You cannot stop yet: a knowledge delta is required and {problem}. Distill what this session learned into Pai "
            f"Knowledge (search first, decisions as proposals, real sources), then write {path} as "
            '{"nodes": ["<node id or slug>", ...]} with at least one node you created or changed.')}

    def test_blocks_without_a_delta_marker(self) -> None:
        self.assertEqual(self.run_hook("stop.py", "stop"), self.blocked("the marker file does not exist"))

    def test_keeps_blocking_when_the_stop_hook_is_already_active(self) -> None:
        self.assertEqual(self.run_hook("stop.py", "stop-active"), self.blocked("the marker file does not exist"))

    def test_blocks_a_marker_with_no_node_reference(self) -> None:
        for data in ({"nodes": []}, {"nodes": ["  ", 3]}, {"other": ["dec-1"]}, ["dec-1"]):
            with self.subTest(data=data):
                path = self.marker(data)
                self.assertEqual(self.run_hook("stop.py", "stop"), self.blocked('the marker has no node reference in its "nodes" list'))
                shutil.rmtree(path.parent)

    def test_blocks_a_marker_that_is_not_json(self) -> None:
        self.marker("not json")
        self.assertEqual(self.run_hook("stop.py", "stop"), self.blocked("the marker file is not valid JSON"))

    def test_allows_stopping_with_one_node_reference(self) -> None:
        self.marker({"nodes": ["decision/acme-uses-cas"]})
        self.assertIsNone(self.run_hook("stop.py", "stop"))

    def test_a_marker_of_another_agent_does_not_count(self) -> None:
        self.marker({"nodes": ["decision/acme-uses-cas"]})
        self.assertEqual(self.run_hook("stop.py", "stop", PAI_HARNESS_AGENT="acme-8")[ "decision"], "block")

    def test_without_a_role_it_does_nothing(self) -> None:
        self.assertIsNone(self.run_hook("stop.py", "stop", PAI_HARNESS_ROLE=None))

    def test_stop_never_loops_it_allows_after_three_blocks_and_writes_a_missing_marker(self) -> None:
        for attempt in (1, 2, 3):
            self.assertEqual(self.run_hook("stop.py", "stop")["decision"], "block", attempt)
            self.assertEqual(self.deltas("acme-7.blocks").read_text().strip(), str(attempt))
            self.assertFalse(self.deltas("acme-7.missing").exists())
        self.assertIsNone(self.run_hook("stop.py", "stop"))  # the fourth stop goes through
        missing = json.loads(self.deltas("acme-7.missing").read_text())
        self.assertEqual((missing["agent"], missing["blocks"], missing["problem"]), ("acme-7", 3, "the marker file does not exist"))
        self.assertIsNone(self.run_hook("stop.py", "stop"))  # and keeps going through: a claude -p run ends

    def test_the_block_count_is_per_agent_and_a_valid_delta_clears_it(self) -> None:
        for _ in range(2):
            self.run_hook("stop.py", "stop")
        self.assertEqual(self.run_hook("stop.py", "stop", PAI_HARNESS_AGENT="acme-8")["decision"], "block")
        self.assertEqual(self.deltas("acme-8.blocks").read_text().strip(), "1")
        path = self.deltas("acme-7.json")
        path.write_text(json.dumps({"nodes": ["decision/acme-uses-cas"]}))
        self.assertIsNone(self.run_hook("stop.py", "stop"))
        self.assertFalse(self.deltas("acme-7.blocks").exists())

    def test_a_valid_delta_removes_an_old_missing_marker(self) -> None:
        for _ in range(4):
            self.run_hook("stop.py", "stop")
        self.assertTrue(self.deltas("acme-7.missing").exists())
        self.deltas("acme-7.json").write_text(json.dumps({"nodes": ["decision/acme-uses-cas"]}))
        self.assertIsNone(self.run_hook("stop.py", "stop"))
        self.assertFalse(self.deltas("acme-7.missing").exists())

    def test_if_the_count_cannot_be_kept_the_stop_is_allowed(self) -> None:
        self.state.mkdir()
        (self.state / "deltas").write_text("a file where the directory should be")
        self.assertIsNone(self.run_hook("stop.py", "stop"))


class WriteZoneTest(HookCase):
    CONTRACTS = ("Write zone: packages/contracts/api.ts belongs to zone 'contracts', owned by acme-lead. It is a ROOT zone: the change needs "
                 "the orchestrator's ROOT go. Your zones: frontend. File a zone request with the owner instead of writing it.")

    def test_a_write_in_my_zone_is_allowed(self) -> None:
        self.assertIsNone(self.pre("write-in-zone"))
        self.assertIsNone(self.pre("bash-redirect-in-zone"))

    def test_a_write_in_another_zone_is_denied_with_the_owner_named(self) -> None:
        self.assertEqual(self.pre("write-other-zone"), deny(self.CONTRACTS))

    def test_an_edit_of_a_root_file_is_denied(self) -> None:
        self.assertEqual(self.pre("edit-other-zone"), deny(
            "Write zone: AGENTS.md belongs to zone 'contracts', owned by acme-lead. It is a ROOT zone: the change needs the orchestrator's ROOT go. "
            "Your zones: frontend. File a zone request with the owner instead of writing it."))

    def test_a_bash_redirect_and_a_tee_outside_the_zone_are_denied(self) -> None:
        self.assertEqual(self.pre("bash-redirect-other-zone"), deny(self.CONTRACTS))
        self.assertEqual(self.pre("bash-tee-other-zone"), deny(self.CONTRACTS.replace("api.ts", "out.txt")))

    def test_a_path_in_no_zone_is_denied_when_the_role_has_zones(self) -> None:
        self.assertEqual(self.pre("write-unzoned"), deny(
            "Write zone: scripts/tool.sh is outside your zones (frontend) and no declared zone covers it. "
            "File a zone request with your lead instead of writing it."))

    def test_a_role_with_no_zones_is_only_kept_out_of_declared_zones(self) -> None:
        self.assertIsNone(self.pre("write-unzoned", PAI_HARNESS_ZONES=""))
        self.assertEqual(self.pre("write-other-zone", PAI_HARNESS_ZONES="")["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_zones_follow_the_owner_list_when_none_are_assigned(self) -> None:
        self.assertIsNone(self.pre("write-in-zone", PAI_HARNESS_ZONES="", PAI_HARNESS_AGENT="acme-app-owner"))
        self.assertEqual(self.pre("write-in-zone", PAI_HARNESS_ZONES="contracts")["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_the_state_dir_and_reads_are_never_blocked(self) -> None:
        self.assertIsNone(self.pre("write-delta-marker"))
        self.assertIsNone(self.pre("bash-read-only"))
        self.assertIsNone(self.pre("bash-status"))

    def test_without_a_role_it_does_nothing(self) -> None:
        for name in ("write-other-zone", "bash-push", "bash-redirect-other-zone"):
            self.assertIsNone(self.pre(name, PAI_HARNESS_ROLE=None), name)

    def test_a_missing_config_fails_closed_for_writes(self) -> None:
        (self.project / ".pai-harness.toml").unlink()
        out = self.pre("write-in-zone")
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("harness config could not be loaded", out["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIsNone(self.pre("bash-status"))


class PushBypassTest(HookCase):
    """Every spelling of a push is refused outside the wrapper; --no-verify is refused even through it."""
    DIRECT = "Direct git push is refused. Push through the push queue wrapper (queue-push.sh)."
    NO_VERIFY = ("git push --no-verify (or a core.hooksPath override) is refused, even through the push queue wrapper. "
                 "Fix what the pre-push hook reports instead of bypassing it.")

    def setUp(self) -> None:
        super().setUp()
        git = ["git", "-c", "init.defaultBranch=main"]
        subprocess.run([*git, "init", "-q", str(self.project)], check=True, env={**self.env})
        for name, value in (("pp", "push"), ("pp2", "pp -u"), ("sp", "!git push")):
            subprocess.run(["git", "-C", str(self.project), "config", f"alias.{name}", value], check=True, env={**self.env})

    def test_every_direct_spelling_is_refused(self) -> None:
        for name in ("push-abs-path", "push-git-dir", "push-env", "push-command", "push-env-assign", "push-sudo-nice", "push-eval",
                     "push-alias", "push-alias-shell", "push-alias-chain", "push-inline-alias"):
            with self.subTest(name=name):
                self.assertEqual(self.pre(f"bash-{name}"), deny(self.DIRECT))

    def test_the_alias_is_read_from_the_git_config(self) -> None:
        subprocess.run(["git", "-C", str(self.project), "config", "--unset", "alias.pp"], check=True, env={**self.env})
        self.assertIsNone(self.pre("bash-push-alias"))  # no longer an alias: `git pp` is not a push

    def test_a_push_alias_in_the_global_config_is_refused_too(self) -> None:
        subprocess.run(["git", "-C", str(self.project), "config", "--unset", "alias.pp"], check=True, env={**self.env})
        Path(self._tmp.name, ".gitconfig").write_text("[alias]\n\tpp = push\n")
        self.assertEqual(self.pre("bash-push-alias"), deny(self.DIRECT))

    def test_no_verify_is_refused_direct_and_through_the_wrapper(self) -> None:
        for name in ("push-no-verify-direct", "push-no-verify-wrapper", "push-no-verify-abbrev", "push-hooks-path"):
            with self.subTest(name=name):
                self.assertEqual(self.pre(f"bash-{name}"), deny(self.NO_VERIFY))

    def test_a_wrapper_push_with_an_env_prefix_is_allowed(self) -> None:
        self.assertIsNone(self.pre("bash-push-wrapper-env"))
        self.assertIsNone(self.pre("bash-push-wrapper"))


class PushKeywordTest(HookCase):
    """A shell keyword may open a segment (`for ...; do CMD; done`); the command after it is judged as if the keyword were not there."""
    DIRECT = "Direct git push is refused. Push through the push queue wrapper (queue-push.sh)."
    NO_VERIFY = PushBypassTest.NO_VERIFY

    def test_the_wrapper_in_a_loop_or_a_conditional_is_allowed(self) -> None:
        for name in ("push-loop-wrapper", "push-keywords-wrapper"):
            with self.subTest(name=name):
                self.assertIsNone(self.pre(f"bash-{name}"))

    def test_every_direct_form_behind_a_keyword_is_refused(self) -> None:
        for name in ("push-loop-direct", "push-then-direct", "push-keywords-direct", "push-loop-wrapper-then-direct", "push-loop-env-direct",
                     "push-loop-fake-wrapper"):
            with self.subTest(name=name):
                self.assertEqual(self.pre(f"bash-{name}"), deny(self.DIRECT))

    def test_no_verify_behind_a_keyword_is_refused_even_through_the_wrapper(self) -> None:
        self.assertEqual(self.pre("bash-push-loop-no-verify"), deny(self.NO_VERIFY))

    def test_keywords_only_expose_the_command_they_never_exempt_it(self) -> None:
        for name in ("keyword-for-direct", "keyword-while-abs-direct"):
            with self.subTest(name=name):
                self.assertEqual(self.pre(f"bash-push-{name}"), deny(self.DIRECT))
        self.assertEqual(self.pre("bash-push-keyword-if-no-verify-direct"), deny(self.NO_VERIFY))

    def test_without_a_wrapper_the_loop_form_is_refused(self) -> None:
        self.assertEqual(self.pre("bash-push-loop-wrapper", PAI_HARNESS_PUSH_WRAPPER=None)["hookSpecificOutput"]["permissionDecision"], "deny")


class PushTest(HookCase):
    DIRECT = "Direct git push is refused. Push through the push queue wrapper (queue-push.sh)."

    def test_a_direct_push_is_refused(self) -> None:
        self.assertEqual(self.pre("bash-push"), deny(self.DIRECT))

    def test_a_push_inside_a_chain_or_a_shell_is_refused(self) -> None:
        self.assertEqual(self.pre("bash-push-chained"), deny(self.DIRECT))
        self.assertEqual(self.pre("bash-push-shell"), deny(self.DIRECT))

    def test_a_push_through_the_wrapper_is_allowed(self) -> None:
        self.assertIsNone(self.pre("bash-push-wrapper"))

    def test_a_direct_push_after_a_wrapper_call_is_still_refused(self) -> None:
        self.assertEqual(self.pre("bash-push-wrapper-then-direct"), deny(self.DIRECT))

    def test_without_a_wrapper_every_push_is_refused(self) -> None:
        self.assertEqual(self.pre("bash-push", PAI_HARNESS_PUSH_WRAPPER=None), deny(
            "Direct git push is refused. No push queue wrapper is configured, so ask your parent to push."))
        self.assertEqual(self.pre("bash-push-wrapper", PAI_HARNESS_PUSH_WRAPPER=None)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_a_missing_config_fails_closed_for_pushes(self) -> None:
        (self.project / ".pai-harness.toml").unlink()
        out = self.pre("bash-push-wrapper")
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("harness config could not be loaded", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_text_that_only_mentions_push_is_allowed(self) -> None:
        self.assertIsNone(self.pre("bash-status"))


if __name__ == "__main__":
    unittest.main()
