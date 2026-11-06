Stdlib-only helper scripts. Every script reads `.pai-harness.toml` through `harness_config.py` (`--config`, `PAI_HARNESS_CONFIG`, or the nearest file upward) and has `--dry-run`.

- `validate_config.py`, `load_config.py`: the config validator and loader.
- `launch.sh`: one issue as `claude -p --output-format stream-json --verbose`, alone or in a Herdr pane. Writes the stream to `runs/<ISSUE>.jsonl` and the verdict (state, cost, turns, session id, exit code) to `runs/<ISSUE>.state.json`. State comes only from the `result` frame and the exit code. Exit 0 done, 1 failed, 2 usage, 3 blocked on a permission. Also `--status`, `--park`, `--resume`.
- `launch.sh ISSUE --profile mechanical --files F... --instruction TEXT`: the mechanical lane. Closed brief, Haiku (`--model sonnet` opts in), `--strict-mcp-config` with an empty MCP config, `--tools`/`--allowed-tools` Read, Edit, Grep, Glob, `--max-turns 12` and `--max-budget-usd 0.25` (override with `[role_limits.mechanical]`), `--output-format json`. Needs a clean git worktree (`--cwd` may be a repository subdirectory: `--files` are relative to it and recorded repo-root-relative); records `profile`, `files`, `base`, `cwd`, `root` and a baseline of the gitignored files for the verifier. The child gets an allowlisted environment (PATH, HOME, locale, Claude sign-in variables; more names via `PAI_HARNESS_LANE_ENV`), no Pai/SSH/cloud credentials, and no `PAI_HARNESS_ROLE`: the plugin hooks do nothing in the lane (it has no Write or MCP to satisfy the Stop delta marker or zones) and the verifier is its guard. Residual risk: `Read` is not confined to the worktree. `--files` entries are literal paths (`[slug]` is fine; `*`, `?` and control characters are refused).
- `verify-mechanical.sh ISSUE (--check CMD | --gate NAME)...`: passes a mechanical run only if it is `done`, the diff (tracked, staged, untracked and gitignored-since-launch) touches only the listed files and every check passes; the scope is measured again after the checks. Otherwise restores the changed paths (`--keep` to leave them) and exits 1. Fails closed: a git failure or timeout writes a `discard` verdict (replacing any earlier pass) and a `BLOCKER`. `--dry-run` never prints `pass` (verdict `unverified`, exit 1). Marks every 5th passing run (a persistent counter in the state dir; `--sample-every` accepts 1 to 5, only stricter) for a Sonnet review.
- `task-done.sh`: closes only a `done` run, and prints the three-line status. A mechanical run also needs a passing verify verdict that still matches the tree (same HEAD and changed content), and, when sampled, `--sample-reviewed REVIEW_FILE`: JSON with `reviewer`, `verdict: clean` and the `diff_sha256` of the verify verdict.
- `health.sh`: `beat NAME` and `check`; a running entry is stale after 15 minutes (exit 1; 2 for an empty registry).
- `dispatcher.sh`: reads ready lines, honours queue, machine and global limits, launches at most that many.
- `gate-request.sh`: asks `[gates]` for one full 40-character sha; `--run` runs them; `--root` reports ROOT hits.
- `linear-status.sh`: the Done/Next/Blocked comment; posts only when the token env var (`LINEAR_API_KEY`) and `LINEAR_API_URL` are both set.

State dir: `PAI_HARNESS_STATE_DIR`, else `$XDG_STATE_HOME/pai-harness/<pai_project>` (never a temporary directory). Registry entries live in `registry/`, events go through the command in `PAI_HARNESS_MCP_CMD` (one JSON object on stdin) when it is set and works, and otherwise append to `journal.jsonl`. `PAI_HARNESS_CLAUDE` and `PAI_HARNESS_HERDR` override the binaries (tests use fakes).

## Which lane

| Work | Use |
|---|---|
| Fully deterministic (a regex rename, a formatter, a codemod) | a script; no model |
| The same small edit across known files, with a little reading (rename `calc_total` in `src/cart.py` and `src/totals.py`) | the mechanical lane: `launch.sh ACME-12 --profile mechanical ...`, then `verify-mechanical.sh` |
| Issues, reviews, decisions, anything that needs a command, the network, Pai tools or scope judgment | an interactive session |
