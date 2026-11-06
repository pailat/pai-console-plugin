# Changelog

Every release has an entry. Merged work never stays unversioned for more than one pull request.

## 0.1.1

Pull requests #25 to #34 of this repository:

- #25 Plugin skeleton: second marketplace entry, the `.pai-harness.toml` schema, validator and loader, the Acme example, the Codex package and the real-identifier denylist test.
- #26 Commands and scripts: `/task-start`, `/task-done`, `/gate`, `/root-review`, `/park`, `/resume`, the `claude -p` launcher (state from the stream-json result frame and the exit code), health check, dispatcher, gate request and Linear status.
- #27 Herdr plugins: the orchestration wake plugin and the new turn recorder (one JSONL journal per turn, replay-safe keys).
- #28 Role skills and agent definitions for eight roles (relay, orchestrator, lead, implementer, root-reviewer, integrator, mechanical, watcher).
- #29 Hooks, inert until the launcher exports a role: SessionStart context, Stop knowledge delta, PreToolUse write zones and push guard.
- #30 Distiller and gate-triager agents with the delta marker helper.
- #31 Hook activation: bounded Stop retry (three blocks, then a `.missing` marker), every direct-push bypass form refused, `rules.push_wrapper`, role zones and the launcher exports.
- #32 Role model defaults aligned with the v4 roles decision; the watcher has no model.
- #33 `gates.hotfix` profile for the red-release hotfix lane, with a decision output the caller can act on.
- #34 Stop-time zone diff: the worktree is diffed against the agent's zones, so `sed -i`, `cp`, `mv` and script writes are caught.
