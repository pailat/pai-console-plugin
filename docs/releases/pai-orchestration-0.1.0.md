# Pai Orchestration 0.1.0

Release preparation date: 2026-11-03, America/Mexico_City. Draft; not published.

## Changes since 0.0.11

- **Herdr skill dependency (ATE-709).** New marketplace entry `herdr`: source `git-subdir`, `https://github.com/herdrdev/herdr.git`, path `skills/herdr`, `ref` `v0.9.5`, `sha` `2ecf19a92fc3a7fff75b6ce3655ef04f4625ec01` (the annotated tag object is `7573e821895d32c8d1f78b3f6c9a2f85a46df4ac`). The new plugin `pai-orchestration` declares `dependencies: ["herdr"]`; `pai-console` has none, so a herdr fetch problem cannot disable the Pai MCP or skills. The URL is the full HTTPS form on purpose: the `owner/repo` shorthand clones over SSH, which fails on machines without a github.com host key.
- **Codex.** The `pai-console` Codex packages are unchanged and do not carry herdr or the orchestration skill. `vendor/herdr` keeps the pinned upstream skill with a sha256 record, and `tools/build_codex.py` fails on drift from the marketplace pin; `tools/vendor_herdr.py` refreshes it. Codex users install the skill with `npx skills add herdrdev/herdr --skill herdr -g`.
- **New plugin `pai-orchestration` 0.1.0** (`plugins/orchestration`), carrying the skill `orchestration` (English, generic): never go idle with work in flight, report to the parent named in the brief, close with a handoff, and use the wake plugin. Roles and process come from the brief and the organization's decision records.
- **New Herdr plugin `herdr-plugins/orchestration-wake`** (event hooks; installed with `herdr plugin install`, not by Claude Code). It never wakes the pane itself, sends each target at most one wake per interval (default 60 s) and does not repeat a `blocked` wake. The example host aliases in `config.env.example` are placeholders.
- **Versions.** `pai-orchestration` starts at 0.1.0. `pai-console` stays at 0.0.11: its skills, agents, hooks, manifest and Codex packages are byte-identical to main, so a bump would only push an empty update to every installation.

## What this release does not establish

No tag or release is published. The herdr versions on the three machines are aligned separately. Fresh-install acceptance, real OAuth and desktop checks are recorded in the issue evidence, not here.
