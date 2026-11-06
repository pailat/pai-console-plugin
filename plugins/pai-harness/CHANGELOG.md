# Changelog

Every release has an entry. Merged work never stays unversioned for more than one pull request.

## Unreleased (cost)

- Every run carries `--max-turns` and `--max-budget-usd` from `[limits]` (`max_turns` 80, `max_budget_usd` 3): a cap stop ends the run `failed`, never `done`.
- The run record adds `model`, token totals (input, cache write, cache read, output) and `peak_context_tokens`; one `run.compaction_alert` journal event and a render line when the context first crosses `limits.compaction_alert_tokens` (120000).
- `cost_report.sh`: per-day totals by role and model from the run records, cost per merged PR with `--merged N`; unpriced runs are counted apart, never as zero.
- Caps are per role: `[role_limits.<role>]` (`max_turns`, `max_budget_usd`) over `[limits]`; defaults give relay and orchestrator 400 turns / $15, lead 300 / $10 and root-reviewer 120 / $8, every other role the `[limits]` values. `max_budget_usd` must be finite and at least 0.01.
- The caps bound the total per issue: the run record holds totals over every invocation (`runs` lists each one), a resume is given only the turns and dollars left, and a capped issue is not resumed (BLOCKER, record untouched) until its cap is raised.
- Usage accounting skips subagent (sidechain) frames, the compaction alert re-arms after the context falls, the record adds `model_reported` from the init frame, and `cost_report.sh` validates `--day` (UTC) and `--merged`, prints the unpriced count in the total and marks cost per merged PR a lower bound when runs are unpriced.
- Default model routing: relay and orchestrator move from Opus to Sonnet; Opus stays only for root-reviewer.

## 0.1.3

Pull requests #40 to #44:

- #40 Every `claude -p` run is visible in Herdr: a readable live render of the stream, workspace metadata with a TTL so a dead run goes stale, and a tab label with the task and state.
- #41 Knowledge target in the config (`[knowledge]`, optional per-stream overrides): the launcher exports it, the distiller has the Knowledge tools and fails closed with a named blocker when no target resolves.
- #42 The Stop zone diff uses the launch base (`PAI_HARNESS_BASE`, `[project] base_branch` fallback), its block text is capped at ten paths, and the push guard accepts a wrapper push behind a shell keyword while every bypass form stays refused.
- #43 Machine token for headless Pai MCP: a header helper that reads a 0600 token file, a strict machine MCP config, and a launcher check that fails closed unless the Pai MCP is connected.
- #44 Distiller read-only mode: with a read-only token a Knowledge write ends in the named blocker `knowledge write needs a project-scope write token`, and a saved report is never a valid delta.

## 0.1.2

Pull requests #35 and #37, and one skill rule:

- #35 Launcher self-check: every `claude -p` run must show the pai-harness skills and hooks in its init event, or the launcher fails closed with a blocker line.
- #37 A writing role (implementer, mechanical, integrator) with no zones blocks at Stop within the three-block bound, and the launcher refuses a writing role outside a git worktree.
- Implementer skill: tests use literal imports only, because a repository scan may refuse a dynamic import or require with a computed path.

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
