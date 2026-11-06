#!/usr/bin/env python3
"""Knowledge delta helper: plan a delta without duplicates, write the Stop-hook marker, and route a failed gate. Stdlib only.

Commands (all print JSON or a note on stdout; exit 0 ok, 1 invalid input, 2 usage):
  plan CANDIDATES.json EXISTING.json   check candidate nodes and drop any that already exist; prints the plan
  write AGENT REF [REF ...]            validate the node references and write <state dir>/deltas/AGENT.json
  triage GATE_OUTPUT.txt               route a failed gate's output to the zone owner (three-line note)

CANDIDATES.json: {"turn": "<turn record id>", "nodes": [{"ref", "kind", "title", "summary", "status", "sources"}]}.
EXISTING.json: the nodes a Knowledge search returned: [{"id", "slug", "kind", "title"}]. The marker is
{"nodes": [...]}, the shape the Stop hook requires. Decision-like kinds must be proposed; sources must be real.

plan and write fail closed: with no Knowledge target (PAI_HARNESS_KNOWLEDGE_ORG plus _PROJECT or _PRODUCT from the launcher,
else [knowledge] in the config for PAI_HARNESS_STREAM) they print `BLOCKER <agent>: no knowledge target resolved for
ROLE/STREAM` and exit 1, so a distiller never writes a delta that has nowhere to go.
"""
from __future__ import annotations

import argparse
import json
import re
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_config  # noqa: E402
import harness_lib as lib  # noqa: E402
from linear_status import compose as lib_compose  # noqa: E402

PROPOSED_KINDS = frozenset(("objective", "decision", "adr", "business_rule", "constraint"))
# Allowed keys per source type; sources are strict, extra keys are refused.
SOURCES = {
    "page": ({"pageId"}, {"quote"}),
    "page_comment": ({"pageId", "threadId"}, set()),
    "url": ({"url", "accessedAt"}, set()),
    "repo": ({"path"}, {"ref"}),
    "chat": (set(), set()),
    "meeting": ({"title", "date"}, set()),
    "ckl": ({"blockId"}, set()),
}
PLACEHOLDER = re.compile(r"^(?:todo|tbd|n/?a|none|unknown|\.\.\.|<.*>)$", re.I)


class DeltaError(ValueError):
    """A plan or marker problem; the message says what to fix."""


def normalize(title: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", title.casefold()).split())


def check_source(where: str, source: object) -> None:
    if not isinstance(source, dict) or source.get("type") not in SOURCES:
        raise DeltaError(f"{where}: source type must be one of {', '.join(SOURCES)}")
    required, optional = SOURCES[source["type"]]
    keys = set(source) - {"type"}
    if keys - required - optional:
        raise DeltaError(f"{where}: unexpected keys {sorted(keys - required - optional)}")
    for key in sorted(required):
        value = source.get(key)
        if not isinstance(value, str) or not value.strip() or PLACEHOLDER.match(value.strip()):
            raise DeltaError(f"{where}: {key} must be a real value, not a placeholder")


def check_node(index: int, node: object, turn: str) -> dict:
    where = f"nodes[{index}]"
    if not isinstance(node, dict):
        raise DeltaError(f"{where}: must be an object")
    for key in ("ref", "kind", "title", "summary"):
        if not isinstance(node.get(key), str) or not node[key].strip():
            raise DeltaError(f"{where}.{key}: required, non-empty string")
    if not node["ref"].startswith("$"):
        raise DeltaError(f"{where}.ref: a local ref starts with $")
    if node["kind"] in PROPOSED_KINDS and node.get("status") != "proposed":
        raise DeltaError(f"{where}.status: a {node['kind']} is created as proposed; a person confirms it")
    sources = node.get("sources")
    if not isinstance(sources, list) or not sources:
        raise DeltaError(f"{where}.sources: at least one real source")
    for number, source in enumerate(sources):
        check_source(f"{where}.sources[{number}]", source)
    if not any(s.get("type") == "chat" or turn in json.dumps(s) for s in sources):
        raise DeltaError(f"{where}.sources: cite the turn record {turn!r} (a chat source or a source naming it)")
    return node


def plan(candidates: object, existing: object) -> dict:
    """Return {"create", "skipped", "marker_hint"}: new nodes to batch, duplicates dropped, and the refs the marker can name."""
    if not isinstance(candidates, dict) or not isinstance(candidates.get("turn"), str) or not candidates["turn"].strip():
        raise DeltaError('candidates: {"turn": "<turn record id>", "nodes": [...]} is required')
    if not isinstance(candidates.get("nodes"), list) or not candidates["nodes"]:
        raise DeltaError("candidates.nodes: at least one node")
    if not isinstance(existing, list):
        raise DeltaError("existing: the list of nodes the Knowledge search returned")
    known = {(normalize(str(n.get("title", ""))), n.get("kind")): n for n in existing if isinstance(n, dict)}
    seen: set[tuple[str, str]] = set()
    create, skipped = [], []
    for index, raw in enumerate(candidates["nodes"]):
        node = check_node(index, raw, candidates["turn"])
        key = (normalize(node["title"]), node["kind"])
        match = known.get(key)
        if match is not None:
            skipped.append({"ref": node["ref"], "title": node["title"], "duplicate_of": match.get("id") or match.get("slug")})
        elif key in seen:
            skipped.append({"ref": node["ref"], "title": node["title"], "duplicate_of": "another candidate in this delta"})
        else:
            seen.add(key)
            create.append(node)
    existing_refs = [s["duplicate_of"] for s in skipped if s["duplicate_of"] != "another candidate in this delta"]
    return {"turn": candidates["turn"], "create": create, "skipped": skipped, "marker_hint": existing_refs}


def validate_refs(refs: list[str]) -> list[str]:
    clean = [r.strip() for r in refs if isinstance(r, str) and r.strip()]
    if not clean:
        raise DeltaError("the marker needs at least one node id or slug")
    local = [r for r in clean if r.startswith("$")]
    if local:
        raise DeltaError(f"{local[0]} is a local ref; write the marker with the node id or slug the batch returned")
    return list(dict.fromkeys(clean))


def write_marker(state: Path, agent: str, refs: list[str]) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", agent or ""):
        raise DeltaError("the agent name is the file name; use letters, digits, dot, dash or underscore")
    path = state / "deltas" / f"{agent}.json"
    lib.write_json(path, {"nodes": validate_refs(refs)})
    return path


def knowledge_target(config_path: str | None, env: dict | None = None, agent: str | None = None) -> dict:
    """The Knowledge target this run writes to, or DeltaError with the named BLOCKER (fail closed).

    The launcher's exports win; without them the config's [knowledge] is resolved for PAI_HARNESS_STREAM.
    """
    env = os.environ if env is None else env
    org, project, product = (env.get(k) for k in ("PAI_HARNESS_KNOWLEDGE_ORG", "PAI_HARNESS_KNOWLEDGE_PROJECT", "PAI_HARNESS_KNOWLEDGE_PRODUCT"))
    stream = env.get("PAI_HARNESS_STREAM") or None
    if org and bool(project) != bool(product):
        return {"organization": org, **({"project": project} if project else {"product": product}), "stream": stream}
    target, config = None, None
    try:
        config, _ = lib.load_config(config_path)
        target = harness_config.resolve_knowledge(config, stream)
    except SystemExit:
        pass  # an unreadable config resolves nothing
    if target:
        return target
    agent = agent or env.get("PAI_HARNESS_AGENT") or "distiller"
    reason = f"no knowledge target resolved for {env.get('PAI_HARNESS_ROLE') or 'distiller'}/{stream or 'default'}"
    if config is not None:
        lib.blocker(lib.state_dir(config), agent, reason)  # journals and prints `BLOCKER <agent>: <reason>`
    else:
        print(f"BLOCKER {agent}: {reason}")
    raise DeltaError(reason)


def owners_for(paths: list[str], zones: dict) -> list[tuple[str, list[str], bool]]:
    """Zones (name, owners, root) whose globs match any path; the first match decides each path."""
    found: dict[str, tuple[str, list[str], bool]] = {}
    for path in paths:
        for name, zone in zones.items():
            if lib.matches(path, zone["globs"]):
                found.setdefault(name, (name, zone["owners"], zone["root"]))
                break
    return list(found.values())


PATH = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+)(?::\d+)?")


def triage(output: str, config: dict) -> str:
    """The three-line triage note for a failed gate: Done (what failed), Next (owner and step), Blocked."""
    paths = list(dict.fromkeys(m.group(1) for m in PATH.finditer(output)))
    hits = owners_for(paths, config.get("zones", {}))
    lines = [line.strip() for line in output.splitlines()]
    failing = [line for line in lines if re.search(r"\b(error|fail|failed|assert\w*)\b|\b[A-Z]+\d{3}\b", line, re.I)]
    first = next((line for line in failing if PATH.search(line)), failing[0] if failing else "no error line found")
    done = f"gate failed: {first[:160]}"
    if not hits:
        return lib_compose(done, "no zone matches the failing paths; ask the lead to assign an owner and re-run the gate", "owner unknown")
    zone, owners, root = hits[0]
    who = ", ".join(owners) if owners else f"the lead (zone {zone} has no owner)"
    where = ", ".join(p for p in paths if lib.matches(p, config["zones"][zone]["globs"]))
    step = f"{who} fixes {where} in zone {zone}, then re-run the gate on the new sha"
    if root:
        step += "; zone is ROOT, so a go/no-go is needed before merge"
    extra = f"also touches zones {', '.join(h[0] for h in hits[1:])}" if len(hits) > 1 else "none"
    return lib_compose(done, step, extra)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="delta_marker.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("candidates")
    p.add_argument("existing")
    w = sub.add_parser("write")
    w.add_argument("agent")
    w.add_argument("refs", nargs="+")
    t = sub.add_parser("triage")
    t.add_argument("output")
    args = parser.parse_args(argv)
    try:
        if args.command in ("plan", "write"):
            knowledge_target(args.config, agent=getattr(args, "agent", None))
        if args.command == "plan":
            lib.show(plan(json.loads(Path(args.candidates).read_text()), json.loads(Path(args.existing).read_text())))
        elif args.command == "write":
            config, _ = lib.load_config(args.config)
            print(write_marker(lib.state_dir(config), args.agent, args.refs))
        else:
            config, _ = lib.load_config(args.config)
            print(triage(Path(args.output).read_text(), config))
    except (DeltaError, OSError, json.JSONDecodeError) as error:
        print(f"invalid: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
