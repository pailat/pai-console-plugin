---
description: Ask the configured gates for one exact commit
argument-hint: <full-40-char-sha> [gate-name] [ISSUE-ID]
allowed-tools: Bash
---

Request a gate for `$ARGUMENTS`.

1. Resolve the sha yourself with `git rev-parse HEAD` on the pushed commit. Branch names and abbreviations are refused: a gate result is evidence only for the exact commit it ran on.
2. Run `${CLAUDE_PLUGIN_ROOT}/scripts/gate-request.sh --sha <sha> [--gate <name>] [--issue <ISSUE-ID>]`. The commands come from `[gates]` in `.pai-harness.toml`.
3. To run the gate in this checkout, add `--run --cwd <dir>`. It refuses if the checkout is not at that sha, and records PASS or FAIL for the sha.
4. Report the sha and the verdict together.
