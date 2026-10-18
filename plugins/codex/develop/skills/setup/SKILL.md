---
name: setup
description: "Set up a Pai Console Codex package, inspect activation and explain OAuth and hook review."
---

# Set up Pai Console

Resolve the absolute directory of this loaded SKILL.md from the skill loader's
reported path, and set the shell variable pai_skill_dir to it (quote the path).
Do not derive it from the session working directory or assume a source checkout.
Read `../../environment.json` relative to this loaded skill directory. Use
`../pai-env/SKILL.md` to inspect activation. Run
`python3 "$pai_skill_dir/../../tools/codex_plugin.py" setup <environment> --dry-run`,
substituting this package's environment. Apply setup only when the user requested
setup, using the same absolute helper path without `--dry-run`.
The helper requires the source marketplace root: it resolves configured local
checkouts or the native configured Git snapshot. Pass `--marketplace-root` for
an explicit local root or a matching Git snapshot root. Git updates require the
user to refresh the snapshot with the native marketplace upgrade command first.
Explain which environment and URL are active and the native approval policy:
known reads are approved; known staging/develop writes are approved;
production writes and unknown tools require prompts.
Have the user authenticate the installed connection named by environment.json server_name in the client's MCP
settings using their Pai staff account, OAuth dynamic client registration and
scope `pai:manage`. Do not collect credentials or authenticate automatically.
Have the user review and trust the packaged hooks in the installed client.
Installation alone does not trust hooks. Verify a fresh session, whoami, a known
read, a harmless authorized write in nonproduction, and a production write
approval prompt that is cancelled before execution. These are manual checks;
configuration and simulated hooks alone cannot prove native enforcement.
Read `../pai-console/SKILL.md` before domain work. Preserve search-before-create,
CAS, idempotency and authorization. Use the current session's native model;
the documented model for this package is `gpt-6.1-sol`.
