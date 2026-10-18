# Pai hook runtime interfaces

The Claude adapter remains `hooks.json`, `session_start.py`, and `guard.py`.
It retains the configurable endpoint, production write confirmations, and existing
Claude transcript-based search check. All maintained messages are English.
`policy.py` shares `READ_TOOLS`, `SEARCH_BEFORE_CREATE`, `IRREVERSIBLE`, and
`ATTENTION`; `tools.json` remains the literal upstream inventory.

## Codex packaging contract

Set the generated plugin manifest's `hooks` field explicitly to
`"./hooks/codex_hooks.json"`. The default `hooks/hooks.json` belongs to Claude.
Package all Python files and `tools.json` alongside the Codex manifest. The
packaging adapter must configure native MCP approval policies for production
writes and unknown tools. Hooks never emit `permissionDecision: "ask"`, never
return `allow`, and never substitute for authorization, CAS, or idempotency.

Supply `environment.json` at `PLUGIN_ROOT` with these exact keys:

```json
{
  "environment": "staging",
  "url": "https://mcp-edge-corp-staging.up.railway.app/mcp",
  "plugin_name": "pai-console-staging",
  "server_name": "pai_console_staging"
}
```

`environment` accepts `develop` (or the API alias `development`), `staging`, or
`production`. `plugin_name` must exactly equal `pai-console-<canonical-environment>`:
`pai-console-develop`, `pai-console-staging`, or `pai-console-production`. Generic
`pai-console` and cross-labeled package metadata are rejected. `server_name` must exactly equal
`pai_console_<canonical-environment>`: `pai_console_develop`,
`pai_console_staging`, or `pai_console_production`. The `development` API alias
canonicalizes to `develop`; `pai-console-development` and
`pai_console_development` are rejected. The bundled
MCP transport and native policy path must use this same unique server name.
URLs must use HTTPS,
port 443 or the default, and `/mcp`, without credentials, query, or fragment.
The hostname must exactly match the packaged environment:

| Environment | Hostnames |
| --- | --- |
| develop | `mcp-corp.paitesting.com`, `mcp-edge-corp-develop.up.railway.app` |
| staging | `mcp-edge-corp-staging.up.railway.app` |
| production | `mcp-corp.pai.lat` |

Packaging must bind that unique server name to the packaged URL in the MCP
manifest, and apply native approvals under
`plugins."<plugin-name>@<marketplace>".mcp_servers.<server_name>`. The hook validates
package metadata and namespace; it does not independently attest the client's
effective transport configuration. Do not reuse these server names for unrelated
connections.

The adapter never reads Claude options or user MCP endpoint settings. CRM-only
sessions use the validated packaged endpoint and exact namespace without requiring unavailable
`whoami`. Non-CRM writes require a successful same-server `whoami` reporting the
packaged environment. Missing, unknown, or mismatched identity after a `whoami`
result blocks all writes, including CRM writes, until a successful matching
`whoami`. Unknown Pai tools are denied in every environment.

## Event and state contract

`codex.py` reads one JSON object from stdin. Lifecycle events use
`hook_event_name` and `session_id`. Tool events also require `tool_name` and an
object `tool_input`. `PostToolUse` consumes only `tool_response`; transcripts
are never read by this adapter. Model selection belongs to the caller, not the
hook runtime.

- `SessionStart` reports the fixed endpoint and approval responsibilities. Resume
  preserves existing evidence; a fork with a new session ID starts without it.
- `PreToolUse` denies missing search evidence, unavailable state, unknown tools,
  and identity mismatches. Accepted writes return context without a permission
  decision, leaving native approvals intact. Inventory reads pass.
- `PostToolUse` records successful search results and `whoami.environment` from
  MCP JSON text or `structuredContent`, including Pai `success`/`data` wrappers.
  Missing results, malformed carriers, `isError`, and application failures never
  authorize creation. A failed repeated search revokes its earlier evidence.
- `SessionEnd` clears evidence and persists an ended-session tombstone. Late
  results cannot recreate search authorization for that session ID.

State lives exclusively in the absolute `PLUGIN_DATA/pai-hook-state` directory.
Each key hashes the session ID, exact server prefix, and full packaged endpoint
identity. Stable `flock` files serialize updates; temporary files are flushed
and atomically renamed. Missing state provides no evidence; corrupt state blocks
writes and requires a new session ID. Lock files and tombstones are retained to
avoid races with late events. State contains tool names and environment labels,
not search inputs, results, credentials, or transcripts.

Native local tools (`Bash`, `apply_patch`, `exec`, `exec_command`, `write_stdin`,
and others) pass through. Codex delivers nested code-mode MCP calls through the
same tool hook path; the adapter does not inspect or execute JavaScript.

The only accepted prefix is `mcp__<server_name>__`, for example
`mcp__pai_console_staging__`. Generic `mcp__pai__`, `mcp__pai-console__`, legacy
plugin spellings, and other environments' namespaces are denied. They never
provide identity or search evidence for this package. Pai-like unknown
namespaces are denied, including the single/double underscore and hyphen plugin
forms; unrelated MCP servers pass through. No suffix matching or guessed prefix
conversion is used.

## Verification and client limits

The input/output contract follows the [official Codex hook documentation](https://learn.chatgpt.com/docs/hooks),
including supported PreToolUse denial and PostToolUse feedback shapes. Plugin
hooks require client trust. Callback errors and unsupported output can fail
open; hooks are guardrails, not a complete enforcement boundary.

The optional native test in `../tests/test_codex_runtime.py` installs a temporary
production-named plugin with server `pai_console_production`. It configures
`plugins."pai-console-production@pai-console-runtime-probe".mcp_servers.pai_console_production`
with a `prompt` default and explicit `approve` overrides for known reads. A mock
`gpt-6.1-sol` response calls the tools through native code mode. The test rejects
native write approval requests and checks that only reads reach the local MCP
server. It uses no hook bypass flags and no real model endpoint. Run it with:

```sh
PAI_RUN_CODEX_RUNTIME=1 python3 -m unittest discover -s tests -p test_codex_runtime.py -v
```

Set `PAI_CODEX_RUNTIME_ARTIFACTS` to a new directory to retain native request,
response, config, and MCP-call evidence. Without explicit opt-in the test skips.
Python contract tests cover environment-specific namespaces, production identity
reported on staging (blocking CRM and non-CRM writes), concurrent state writes,
all inventory policies, lifecycle events, malformed results, and isolation.

The native probe passed on Codex CLI **0.163.0** with observed tool names
`mcp__pai_console_production__<tool>`. Known reads `whoami` and `page_read`
reached the mock without prompts. Writes `page_update` and `future_write` each
produced an approval request for `pai_console_production`; rejecting both left
zero writes in the mock MCP log, including when the unknown tool advertised
`readOnlyHint: true`.

Native approval verification is specific to the installed client version and
fixture configuration; it does not establish deployed hook trust. Other client
versions, real OAuth, desktop behavior, and production writes remain untested.
