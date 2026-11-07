Stdlib-only helper scripts. Every script reads `.pai-harness.toml` through `harness_config.py` (`--config`, `PAI_HARNESS_CONFIG`, or the nearest file upward) and has `--dry-run`.

- `validate_config.py`, `load_config.py`: the config validator and loader.
- `agent-start.sh <name> --role R --parent P --pane X [--issue I] [--kind K] -- <agent args>`: `herdr agent start` plus `pai-pane-meta` (name, role, parent, issue, `wake_on_done=1`) in one step. Fails closed: if the start or the tagging fails it prints `FAILED <name>` and exits 1. Agent args pass through unchanged; the permission default lives in `launch.py`. Start interactive agents only through it.
- `launch.sh`: one issue as `claude -p --output-format stream-json --verbose`, alone or in a Herdr pane. Writes the stream to `runs/<ISSUE>.jsonl` and the verdict (state, cost, turns, session id, exit code) to `runs/<ISSUE>.state.json`. State comes only from the `result` frame and the exit code. Exit 0 done, 1 failed, 2 usage, 3 blocked on a permission. Also `--status`, `--park`, `--resume`. It tags its own pane with the pai wake tokens before the run (`--parent P` or `PAI_HARNESS_PARENT`). `health.sh check` warns about agent panes with no pai tokens.
- `task-done.sh`: closes only a `done` run, and prints the three-line status.
- `health.sh`: `beat NAME` and `check`; a running entry is stale after 15 minutes (exit 1; 2 for an empty registry). `check` also warns (`untagged-agent-pane`, exit code unchanged) about Herdr agent panes with no pai tokens.
- `dispatcher.sh`: reads ready lines, honours queue, machine and global limits, launches at most that many.
- `gate-request.sh`: asks `[gates]` for one full 40-character sha; `--run` runs them; `--root` reports ROOT hits.
- `linear-status.sh`: the Done/Next/Blocked comment; posts only when the token env var (`LINEAR_API_KEY`) and `LINEAR_API_URL` are both set.

State dir: `PAI_HARNESS_STATE_DIR`, else `$XDG_STATE_HOME/pai-harness/<pai_project>` (never a temporary directory). Registry entries live in `registry/`, events go through the command in `PAI_HARNESS_MCP_CMD` (one JSON object on stdin) when it is set and works, and otherwise append to `journal.jsonl`. `PAI_HARNESS_CLAUDE` and `PAI_HARNESS_HERDR` override the binaries (tests use fakes).
