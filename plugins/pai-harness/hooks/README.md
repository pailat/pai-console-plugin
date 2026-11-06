Hooks of the harness. They run only when `PAI_HARNESS_ROLE` is set; without it every hook does nothing.

| Event | Script | What it does |
| --- | --- | --- |
| SessionStart | `session_start.py` | Prints the brief (`PAI_HARNESS_BRIEF`) and the curated Knowledge as `additionalContext`. Knowledge comes from the command in `PAI_HARNESS_KNOWLEDGE_CMD`, which reads one JSON object (`role`, `agent`, `session_id`, `project`) on stdin and prints markdown. |
| Stop | `stop.py` | Blocks stopping until `<state dir>/deltas/<agent>.json` holds `{"nodes": [...]}` with at least one node reference. The agent is `PAI_HARNESS_AGENT`, else the session id. |
| PreToolUse | `pre_tool_use.py` | Denies a Write, Edit, MultiEdit, NotebookEdit or Bash redirect/`tee` outside the role's zones, naming the zone owner, and denies a direct `git push`. |

Zones come from `.pai-harness.toml`. The agent's zones are the names in `PAI_HARNESS_ZONES` (comma separated), else the zones that list `PAI_HARNESS_AGENT` as an owner. Paths outside the project root and the state dir are not policed. A push is allowed only when the command starts with the push queue wrapper (`PAI_HARNESS_PUSH_WRAPPER`, or `rules.push_wrapper` once the schema has it). With a role set and no usable config, writes and pushes are denied; Stop and SessionStart do nothing.

The hooks only allow or deny; they never ask. Tests: `python3 -m unittest tests.test_harness_hooks`.
