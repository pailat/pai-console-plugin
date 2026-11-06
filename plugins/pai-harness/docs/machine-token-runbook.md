# Runbook: machine token for headless runs

Audience: the owner of a machine that runs the harness. Every `<placeholder>` below is yours to fill; this file never holds a real value.

## What this does

`claude -p` cannot sign in through the browser, so a headless run has no Pai MCP by default. The harness gives each machine one
service-account token. When `[pai] mcp_url` is set in `.pai-harness.toml`, the launcher:

1. writes a machine-only MCP config (one server, `pai`, with a `headersHelper`) and passes `--mcp-config` plus `--strict-mcp-config`;
2. lets Claude Code run `scripts/mcp_headers.sh`, which reads the token file and prints only `{"Authorization":"Bearer ..."}`;
3. reads the run's `system/init` event and **fails closed** unless the `pai` server is `connected` and its `mcp__pai__*` tools are listed.
   The run is stopped, the journal and stdout get `BLOCKER <ISSUE>: pai mcp not connected: ...`, and the launcher exits non-zero.

Agents never see the value. It is never in git, Linear, Knowledge, the journal, the stream log or the launcher's output.

## Set up (per machine)

1. In the Pai portal, issue one token for the service account `<service-account>` for this machine (`<machine>`).
   The value is shown once. Do not paste it into a chat, an issue or a terminal that is logged.
2. Store it in your password manager as `<vault>/<item>`, field `credential`, with the machine name in the item title.
3. Place it on the machine, with the mode set before the value is written:

   ```sh
   umask 077
   mkdir -p ~/.config/pai-harness
   op read 'op://<vault>/<item>/credential' > ~/.config/pai-harness/token
   chmod 600 ~/.config/pai-harness/token
   ```

   The file must be a regular file (not a symlink), mode `0600`, owned by the user that runs the launcher, and hold the token alone on one line.
   Any other mode or owner is refused. Keep `~/.config/pai-harness` at mode `0700`.
4. Set `[pai] mcp_url` (the corp MCP endpoint) in the project's `.pai-harness.toml`. `token_file` is only needed for a non-default path;
   the environment variable `PAI_HARNESS_TOKEN_FILE` overrides it for one run.
5. Check without a run: `scripts/mcp_headers.sh --config <repo>/.pai-harness.toml >/dev/null; echo $?` prints `0`. Do not drop the `>/dev/null`: stdout is the token.
6. Pilot: start one run and read the init line. The Pai server must show `connected`, and a Knowledge write must be audited as `<service-account>`.

## Refusals you may see

| Message | Cause | Fix |
| --- | --- | --- |
| `token file ... is missing` | no file at the configured path | place it (step 3) |
| `has mode 0644; it must be 0600` | wrong mode | `chmod 600` |
| `is not owned by the current user` | file written by root or another user | rewrite it as the launcher's user |
| `empty or is not a single printable token` | blank file, extra lines or spaces | rewrite it from the password manager |
| `BLOCKER ...: pai mcp not connected` | the server is missing, not `connected`, or lists no tools | read the reason after the colon; check the URL, the token and that it is not revoked |

## Rotate

Rotate on a schedule you choose, and at once after any exposure: use `iam_service_token_rotate` for the account, store the new value
under the same item, and re-run step 3 on every machine that holds the old one. The old value stops working when it is rotated.

## Revoke (a lost machine or a leak)

1. Revoke the token with `iam_service_token_revoke` (or disable the service account for a wider stop).
2. Delete the file on the machine if you still have it: `rm ~/.config/pai-harness/token`.
3. Review the audit log for the account (`iam_audit_list`) from the time of the loss.
4. Issue a new token and place it (Set up).

Until step 4 the launcher fails closed on that machine: runs stop with `pai mcp not connected` instead of falling back to another login.

## Read-only token

A machine whose token cannot write Knowledge sets `[pai] token_scope = "read"` (or `PAI_HARNESS_TOKEN_SCOPE=read`; the launcher exports the config value). The distiller then searches and reads only, saves its proposed nodes with `scripts/delta_marker.py report` as `<state dir>/deltas/<agent>.report.json`, and stops with the BLOCKER `knowledge write needs a project-scope write token`. A write the MCP rejects with permission denied ends the same way (`report --denied`). The Stop hook does not count the report as a delta; the `.missing` marker records `knowledge write blocked: read-only token`. Once a project-scope write token is placed, set the scope back to `write` (the default) and re-run the distiller on the saved report.
