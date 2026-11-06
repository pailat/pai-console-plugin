---
description: Decide whether a change needs ROOT review and request it for the exact sha
argument-hint: <full-40-char-sha> <base-ref> [ISSUE-ID]
allowed-tools: Bash
---

Check ROOT review for `$ARGUMENTS`.

1. List the changed files: `git diff --name-only <base-ref>...<sha>`.
2. Pipe them in: `... | ${CLAUDE_PLUGIN_ROOT}/scripts/gate-request.sh --sha <sha> --root --dry-run`. It reports whether any file falls in a `root = true` zone or in `rules.root_paths`.
3. If `touches_root` is false, say so and stop: the normal gate is enough.
4. If it is true, start the `root-reviewer` role (its model comes from `[models]`) on that exact sha with the matched files, and send your parent one line: `ROOT go/no-go <PR> <sha>: <reviewer verdict>` with the evidence. Merge only after a go.
