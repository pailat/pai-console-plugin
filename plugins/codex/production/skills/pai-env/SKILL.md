---
name: pai-env
description: "Show or switch the installed Pai Console environment; only switch when the user explicitly requests it."
---

# Pai environment

Resolve the absolute directory of this loaded SKILL.md from the skill loader's
reported path. Set the shell variable pai_skill_dir to that directory (quote the
path). Never derive it from the session working directory or assume a checkout.
Run the bundled helper with the shell tool:
`python3 "$pai_skill_dir/../../tools/codex_plugin.py" status`.
With no requested environment, report status and stop. Never switch automatically.
When the user explicitly requests staging, develop, or production, run
`python3 "$pai_skill_dir/../../tools/codex_plugin.py" switch <environment> --dry-run`
first, then run the same command without `--dry-run`. Substitute the requested
environment. Keep the helper path absolute through pai_skill_dir in every call.
For production, explain that native policy requests approval for every write.
The helper installs through native Codex plugin commands and activates exactly
one Pai environment in the selected CODEX_HOME. It never authenticates.
If the source checkout moved, pass `--marketplace-root /absolute/path/to/checkout`.
After a change, request a new session or desktop restart and authentication for
the selected plugin's server_name from environment.json. Tokens are specific to the endpoint.
Read `../../environment.json` for this package's identity; installed activation
comes from helper status, not from this file. Project or managed config can
override user config. Do not claim hooks are trusted or effective native
approvals are verified from a config inspection.
