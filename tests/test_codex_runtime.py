"""Optional native Codex approval probe using only local model/MCP fixtures.

Run explicitly (requires Codex and permission to bind a loopback socket):
  PAI_RUN_CODEX_RUNTIME=1 python3 -m unittest discover -s tests -p test_codex_runtime.py -v

Optional: PAI_CODEX_RUNTIME_ARTIFACTS=/tmp/pai-native-approval-evidence

The fixture installs a temporary production-named plugin into a temporary
CODEX_HOME. It has no hooks and uses no bypass flags. It sends native approval
requests back with action=decline; it never approves requests or controls a UI.
No real model, Pai endpoint, OAuth, user configuration, or Herdr is involved.

Policy under test (official contract: https://learn.chatgpt.com/docs/extend/mcp):
  [plugins."pai-console-production@pai-console-runtime-probe".mcp_servers.pai_console_production]
  default_tools_approval_mode = "prompt"
  [plugins."pai-console-production@pai-console-runtime-probe".mcp_servers.pai_console_production.tools.page_read]
  approval_mode = "approve"

This test establishes native approval behavior for the installed client version,
not deployed hook trust or binding of hook endpoint metadata to an MCP transport.
"""
from __future__ import annotations

import http.server
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

PLUGIN = "pai-console-production"
MARKETPLACE = "pai-console-runtime-probe"
PLUGIN_ID = f"{PLUGIN}@{MARKETPLACE}"
SERVER = "pai_console_production"
MODEL = "gpt-6.1-sol"
READS = ("whoami", "page_read")
WRITES = ("page_update", "future_write")

MCP_SOURCE = r'''
import json
from pathlib import Path
import sys

log = Path(sys.argv[1])
for line in sys.stdin:
    event = json.loads(line)
    if "id" not in event:
        continue
    method = event["method"]
    result = {}
    if method == "initialize":
        result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                  "serverInfo": {"name": "pai-local-approval-fixture", "version": "1"}}
    elif method == "tools/list":
        result = {"tools": [
            {"name": name, "description": "Local approval fixture: " + name,
             "inputSchema": {"type": "object", "properties": {}},
             "annotations": {"readOnlyHint": name != "page_update",
                             "destructiveHint": name == "page_update"}}
            for name in ("whoami", "page_read", "page_update", "future_write")
        ]}
    elif method == "tools/call":
        with log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event["params"]) + "\n")
            stream.flush()
        # Even if a client fails to enforce policy, writes only append to this
        # temporary evidence log; no external action is possible.
        result = {"isError": False, "content": [{"type": "text", "text": json.dumps({
            "success": True, "data": {"environment": "production", "fixture": True}
        })}]}
    print(json.dumps({"jsonrpc": "2.0", "id": event["id"], "result": result}), flush=True)
'''

SCRIPT = '''
text({inventory: ALL_TOOLS.filter(t => t.name.startsWith("mcp__")).map(t => t.name)});
for (const name of ["whoami", "page_read", "page_update", "future_write"]) {
    const tool = ALL_TOOLS.find(t => t.name === "mcp__pai_console_production__" + name);
    if (!tool) throw new Error("Expected native Pai tool missing: " + name);
    try { text({name, result: await tools[tool.name]({})}); }
    catch (error) { text({name, error: String(error)}); }
}
'''


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list:
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class MockModel(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, root: Path):
        self.root = root
        self.requests = []
        super().__init__(("127.0.0.1", 0), ModelHandler)


class ModelHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append(body)
        write_json(self.server.root / f"model-request-{len(self.server.requests)}.json", body)
        if body.get("model") != MODEL or self.path != "/v1/responses":
            self.send_error(400, "Unexpected fixture model or endpoint")
            return
        first = len(self.server.requests) == 1
        if first:
            item = {"type": "custom_tool_call", "id": "call_local_probe",
                    "call_id": "call_local_probe", "namespace": "functions",
                    "name": "exec", "input": SCRIPT}
        else:
            item = {"type": "message", "id": "msg_local_probe", "role": "assistant",
                    "status": "completed", "content": [{"type": "output_text",
                    "text": "Local native approval fixture completed.", "annotations": []}]}
        response = {"id": f"resp_local_{len(self.server.requests)}", "status": "completed",
                    "output": [item], "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
        events = [
            {"type": "response.created", "response": {**response, "status": "in_progress", "output": []}},
            {"type": "response.output_item.added", "output_index": 0, "item": dict(item, input="") if first else item},
        ]
        if first:
            events.append({"type": "response.custom_tool_call_input.delta", "output_index": 0,
                           "item_id": item["id"], "delta": SCRIPT})
        else:
            events.append({"type": "response.output_text.delta", "output_index": 0, "content_index": 0,
                           "item_id": item["id"], "delta": item["content"][0]["text"]})
        events.extend([
            {"type": "response.output_item.done", "output_index": 0, "item": item},
            {"type": "response.completed", "response": response},
        ])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for event in events:
            self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
        self.wfile.flush()


def isolated_environment(home: Path) -> dict:
    # Do not copy account tokens, CODEX_THREAD_ID, OPENAI_BASE_URL, or remote MCP
    # connection settings into the child. HOME itself is never changed.
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "SYSTEMROOT", "TMPDIR") if key in os.environ}
    env["CODEX_HOME"] = str(home)
    return env


def prepare_fixture(root: Path, cli: str) -> tuple[dict, str]:
    home = root / "codex-home"
    home.mkdir()
    env = isolated_environment(home)
    market = root / "market"
    plugin = market / "plugins" / PLUGIN
    server = root / "mock_mcp.py"
    server.write_text(MCP_SOURCE, encoding="utf-8")
    write_json(plugin / ".codex-plugin/plugin.json", {
        "name": PLUGIN, "version": "1.0.0", "description": "Local native approval fixture",
        "mcpServers": "./.mcp.json",
    })
    write_json(plugin / ".mcp.json", {"mcpServers": {SERVER: {
        "command": sys.executable, "args": [str(server), str(root / "mcp-calls.jsonl")],
    }}})
    write_json(market / ".agents/plugins/marketplace.json", {
        "name": MARKETPLACE, "plugins": [{"name": PLUGIN,
        "source": {"source": "local", "path": f"./plugins/{PLUGIN}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity"}],
    })
    logs = []
    for args in (("--version",), ("plugin", "marketplace", "add", str(market), "--json"),
                 ("plugin", "add", PLUGIN_ID, "--json")):
        result = subprocess.run([cli, *args], cwd=root, env=env, text=True,
                                capture_output=True, timeout=25, check=True)
        logs.append({"arguments": list(args), "stdout": result.stdout, "stderr": result.stderr})
    write_json(root / "cli-setup.json", logs)
    config = home / "config.toml"
    config.write_text(f'model = "{MODEL}"\napprovals_reviewer = "user"\n\n' + config.read_text(), encoding="utf-8")
    with config.open("a", encoding="utf-8") as stream:
        stream.write("\n")
        # Top-level model is supplied explicitly on thread/start as well. Policy
        # belongs to the exact installed plugin, not a top-level mcp_servers key.
        stream.write(f'[plugins."{PLUGIN_ID}".mcp_servers.{SERVER}]\n'
                     'default_tools_approval_mode = "prompt"\n')
        for tool in READS + ("page_update",):
            mode = "approve" if tool in READS else "prompt"
            stream.write(f'\n[plugins."{PLUGIN_ID}".mcp_servers.{SERVER}.tools.{tool}]\n'
                         f'approval_mode = "{mode}"\n')
    return env, logs[0]["stdout"].strip()


def run_probe(root: Path, cli: str) -> dict:
    env, version = prepare_fixture(root, cli)
    model = MockModel(root)
    worker = threading.Thread(target=model.serve_forever, daemon=True)
    worker.start()
    events = []
    prompts = []
    responses = []
    setup = []
    transport = queue.Queue()
    process = None
    try:
        arguments = [cli, "app-server", "--stdio", "-c", 'model_provider="local_fixture"',
            "-c", 'model_providers.local_fixture.name="Local fixture"',
            "-c", f'model_providers.local_fixture.base_url="http://127.0.0.1:{model.server_port}/v1"',
            "-c", 'model_providers.local_fixture.wire_api="responses"',
            "-c", "model_providers.local_fixture.request_max_retries=0",
            "-c", "model_providers.local_fixture.stream_max_retries=0"]
        with (root / "app-server-stderr.log").open("w", encoding="utf-8") as stderr:
            process = subprocess.Popen(arguments, cwd=root, env=env, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=stderr, text=True, start_new_session=True)

            def consume():
                for line in process.stdout:
                    transport.put(line)
                transport.put(None)

            threading.Thread(target=consume, daemon=True).start()

            def send(message):
                process.stdin.write(json.dumps(message) + "\n")
                process.stdin.flush()

            def request(identifier, method, params):
                send({"id": identifier, "method": method, "params": params})

            request(100, "initialize", {"clientInfo": {"name": "pai-approval-probe", "version": "1"},
                                      "capabilities": {"experimentalApi": True}})
            deadline = time.monotonic() + 45
            completed = None
            while completed is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Native approval fixture timed out; inspect saved events.")
                try:
                    line = transport.get(timeout=min(remaining, 1))
                except queue.Empty:
                    continue
                if line is None:
                    raise RuntimeError("App-server exited before completing the local fixture.")
                event = json.loads(line)
                events.append(event)
                with (root / "app-server-events.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(event) + "\n")
                if "method" in event and "id" in event:
                    # The ONLY response sent to a native prompt is rejection.
                    # An unexpected request is rejected too and fails validation.
                    prompts.append(event)
                    if event["method"] == "mcpServer/elicitation/request":
                        rejection = {"id": event["id"], "result": {"action": "decline", "content": None}}
                        responses.append(rejection)
                        send(rejection)
                    else:
                        send({"id": event["id"], "error": {"code": -32601, "message": "Unexpected local fixture request; rejected"}})
                    continue
                if event.get("id") in (100, 101, 102, 103) and "error" in event:
                    raise RuntimeError(f"App-server rejected fixture setup: {event}")
                if event.get("id") == 100:
                    request(101, "thread/start", {"cwd": str(root), "model": MODEL,
                        "modelProvider": "local_fixture", "approvalPolicy": "on-request", "sandbox": "read-only"})
                elif event.get("id") == 101:
                    setup.append(event["result"])
                    thread = event["result"]["thread"]["id"]
                    request(102, "mcpServerStatus/list", {})
                elif event.get("id") == 102:
                    setup.append(event["result"])
                    request(103, "turn/start", {"threadId": thread, "input": [{"type": "text",
                        "text": "Exercise only the local mock read/write tools for this approval fixture."}]})
                elif event.get("method") == "turn/completed":
                    completed = event["params"]["turn"]
            result = {"version": version, "model": MODEL, "plugin_id": PLUGIN_ID, "server_name": SERVER,
                "policy_path": f'plugins."{PLUGIN_ID}".mcp_servers.{SERVER}',
                "setup": setup, "prompts": prompts, "prompt_responses": responses, "mcp_calls": read_jsonl(root / "mcp-calls.jsonl"),
                "completed_turn": completed, "model_requests": len(model.requests)}
            write_json(root / "summary.json", result)
            return result
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
        model.shutdown()
        model.server_close()
        worker.join(timeout=2)


@unittest.skipUnless(os.environ.get("PAI_RUN_CODEX_RUNTIME") == "1", "Optional native client probe; set PAI_RUN_CODEX_RUNTIME=1")
class NativeCodexApprovalTest(unittest.TestCase):
    def test_production_plugin_prompts_and_rejection_prevents_writes(self):
        cli = shutil.which("codex")
        self.assertIsNotNone(cli, "The optional runtime probe requires the native codex CLI.")
        destination = os.environ.get("PAI_CODEX_RUNTIME_ARTIFACTS")
        if destination:
            root = Path(destination).resolve()
            root.mkdir(parents=True, exist_ok=False)
        else:
            temporary = tempfile.TemporaryDirectory(prefix="pai-native-approval-")
            self.addCleanup(temporary.cleanup)
            root = Path(temporary.name)
        result = run_probe(root, cli)
        context = f"Installed client {result['version']}; evidence: {root}"
        self.assertEqual(result["setup"][0]["model"], MODEL, context)
        self.assertEqual(result["setup"][0]["approvalsReviewer"], "user", context)
        servers = result["setup"][1]["data"]
        self.assertEqual([(s["name"], s["pluginId"]) for s in servers], [(SERVER, PLUGIN_ID)], context)
        self.assertEqual(result["completed_turn"]["status"], "completed", context)
        self.assertEqual(result["model_requests"], 2, context)
        self.assertEqual([c["name"] for c in result["mcp_calls"]], list(READS), context)
        self.assertEqual(len(result["prompts"]), len(WRITES), context)
        self.assertEqual([r["result"]["action"] for r in result["prompt_responses"]], ["decline"] * len(WRITES), context)
        for request, rejection, tool in zip(result["prompts"], result["prompt_responses"], WRITES):
            self.assertEqual(request["id"], rejection["id"], context)
            self.assertEqual(request["method"], "mcpServer/elicitation/request", context)
            params = request["params"]
            self.assertEqual(params["serverName"], SERVER, context)
            self.assertEqual(params["_meta"]["codex_approval_kind"], "mcp_tool_call", context)
            self.assertIn(f'"{tool}"', params["message"], context)
        # The second model request carries the actual nested-call outputs. Both
        # writes must be rejected rather than silently skipped by the fixture.
        followup = json.loads((root / "model-request-2.json").read_text())
        outputs = [item for item in followup["input"] if item.get("type") == "custom_tool_call_output"]
        self.assertTrue(outputs, context)
        self.assertIn("user rejected MCP tool call", json.dumps(outputs), context)
        print(f"\n{context}\nNative reads received: {list(READS)}; write prompts rejected: {list(WRITES)}; writes received: 0.")


if __name__ == "__main__":
    unittest.main()
