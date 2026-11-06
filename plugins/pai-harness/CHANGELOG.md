# Changelog

Every release has an entry. Merged work never stays unversioned for more than one pull request.

## 0.1.6

Permission policy (pull request #51):

- Every run passes `--permission-mode bypassPermissions` (fresh, `--resume` and dispatch share one command builder); `[run] bypass_permissions = false` opts a project out. With the opt-out `claude -p` has no prompts, so a tool that is not pre-approved is denied and the run ends `blocked`. `--allowed-tools` limits nothing while bypass is on.
- Fail-closed preflight: with bypass on, `launch.sh` reads the effective Claude Code settings (managed, user, project, local) and ends the run `blocked` (exit 3, a named BLOCKER, no process) unless the deny baseline is present (`scripts/deny_baseline.py`). `[run] require_deny_baseline = false` waives it.
- `examples/settings.deny.json` now denies the Pai write tools that change access, deploy, delete or export data and Linear deletes, and its Bash patterns cover `git -C`, `git -c`, `rm -r -f`, `"$HOME"`, `./.git` and `.env` reads. Merge and protected-branch denials moved to `examples/settings.deny.non-merge.json` for the roles that do not merge.
- A permission denial now reads `denied by policy or not pre-approved: <tools>; report BLOCKER, do not work around it`.
- The generated Codex package no longer ships the Claude `settings.deny.json` files; its examples README says the bypass policy is Claude Code only.

## 0.1.5

Pull request #48 (zone hooks no longer fail open):

- The zone root comes from the git top level of the working directory, not from the directory of `PAI_HARNESS_CONFIG`, so a config in another checkout than the agent's worktree no longer turns every worktree path into "outside the project".
- PreToolUse: a write whose target lies under no known root is resolved by its own git top level and common directory; in the config's repository it is judged under that top level (a sibling worktree included), and a failed lookup denies for a writing role. Paths proven outside the repository keep their behavior.
- Stop zone diff: every root is diffed; any git failure, timeout or missing base ends in a named "cannot be checked" verdict, never in "nothing changed", and there is no `HEAD` fallback for the base. Those blocks are not lifted by the three-block bound.
- Accepted as fail-closed: a config in a subdirectory missing from the agent's worktree blocks Stop, and non-writing roles that have zones get the same unbounded Stop block.

## 0.1.4

Pull request #46 (cost levers):

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
