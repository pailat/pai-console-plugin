# Herdr plugins of pai-harness

Install each directory with `herdr plugin install`; both run on Linux and macOS and never fail a Herdr event.

- `orchestration-wake` (`pai.orchestration-wake`): wakes parents and requesters on agent status changes and job-pane exits.
  `bin/pai-pane-meta` sets a pane's tokens and caches them. Same behaviour as the copy in pai-console.
- `turn-recorder` (`pai.turn-recorder`): on `pane.agent_status_changed` and `pane.exited` appends the pane events and the
  stream-json frames of the run to one JSONL file per turn in the plugin state dir (`turns/<pane>-<turn>.jsonl`). It is
  the future degraded-mode journal: append-only, one idempotency `key` per line, so a replay adds no duplicates.
  The stream path is the pane token `stream`, else `PAI_RECORDER_STREAM` (`{name}` and `{pane}` expand); see `config.env.example`.
