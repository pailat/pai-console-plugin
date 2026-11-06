"""Shared definition of the .pai-harness.toml contract: spec, defaults, validation and loading. Stdlib only.

The JSON Schema in schema/pai-harness.schema.json documents the same contract for editors and other tools;
tests keep the two in step. This module is what the plugin runs.
"""
from __future__ import annotations

import copy
import re
import tomllib
from pathlib import Path

CONFIG_NAME = ".pai-harness.toml"
SCHEMA_VERSION = 1
ROLES = ("relay", "orchestrator", "lead", "implementer", "root-reviewer", "integrator",
         "distiller", "gate-triager", "mechanical", "watcher")
MODEL_CHOICES = ("opus", "sonnet", "haiku", "none")  # "none" is only for the watcher, a script
# Role models (the v4 roles decision): Opus for relay, orchestrator and root-reviewer; Haiku for mechanical work behind
# rails; Sonnet for lead, implementer, integrator, distiller and gate-triager; the watcher is a script (no model).
DEFAULT_MODELS = {
    "relay": "opus", "orchestrator": "opus", "lead": "sonnet", "implementer": "sonnet",
    "root-reviewer": "opus", "integrator": "sonnet", "distiller": "sonnet",
    "gate-triager": "sonnet", "mechanical": "haiku", "watcher": "none",
}
DEFAULTS = {
    "schema_version": SCHEMA_VERSION,
    "project": {},
    "gates": {},
    "zones": {},
    "machines": {},
    "queues": {},
    "limits": {"max_agents": 6, "max_agents_per_machine": 3, "max_open_prs": 5, "turn_timeout_minutes": 60},
    "role_zones": {},
    "rules": {"agents_file": "AGENTS.md", "root_paths": [], "must": [], "never": [], "push_wrapper": ""},
    "models": dict(DEFAULT_MODELS),
    "knowledge": {},  # empty = no Pai Knowledge target named; the distiller then fails closed
}
NAME = re.compile(r"^[a-z][a-z0-9_-]*$")
HOTFIX_GATE = "hotfix"  # the one [gates.*] entry that is a typed table; every other gate is a command or a list of commands


class ConfigError(ValueError):
    """A config problem; the message names the offending key path."""


def _type_name(value: object) -> str:
    return {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "table"}.get(type(value), type(value).__name__)


def _expect(path: str, value: object, kind: type, label: str | None = None) -> None:
    if kind is int and isinstance(value, bool) or not isinstance(value, kind):
        raise ConfigError(f"{path}: expected {label or _type_name(kind())}, got {_type_name(value)}")


def _string(path: str, value: object) -> str:
    _expect(path, value, str)
    if not value.strip():  # type: ignore[union-attr]
        raise ConfigError(f"{path}: must not be empty")
    return value  # type: ignore[return-value]


def _strings(path: str, value: object, unique: bool = True) -> list[str]:
    _expect(path, value, list)
    items = [_string(f"{path}[{i}]", item) for i, item in enumerate(value)]  # type: ignore[arg-type]
    if unique and len(set(items)) != len(items):
        raise ConfigError(f"{path}: entries must be unique")
    return items


def _positive(path: str, value: object) -> int:
    _expect(path, value, int)
    if value < 1:  # type: ignore[operator]
        raise ConfigError(f"{path}: must be at least 1, got {value}")
    return value  # type: ignore[return-value]


def _table(path: str, value: object, allowed: set[str], required: set[str] = frozenset()) -> dict:  # type: ignore[assignment]
    _expect(path, value, dict)
    for key in sorted(value):  # type: ignore[arg-type]
        if key not in allowed:
            raise ConfigError(f"{path}.{key}: unknown key (allowed: {', '.join(sorted(allowed))})" if path else f"{key}: unknown section (allowed: {', '.join(sorted(allowed))})")
    for key in sorted(required):
        if key not in value:  # type: ignore[operator]
            raise ConfigError(f"{path}.{key}: required key is missing" if path else f"{key}: required section is missing")
    return value  # type: ignore[return-value]


def _named(path: str, value: object) -> dict:
    _expect(path, value, dict)
    for key in value:  # type: ignore[attr-defined]
        if not NAME.match(key):
            raise ConfigError(f"{path}.{key}: name must be lowercase letters, digits, '-' or '_' and start with a letter")
    return value  # type: ignore[return-value]


def validate(data: object) -> dict:
    """Return the config with defaults applied, or raise ConfigError naming the first bad key."""
    top = {"schema_version", "project", "gates", "zones", "machines", "queues", "limits", "rules", "models", "role_zones", "knowledge"}
    data = _table("", data, top, {"project"})
    out = copy.deepcopy(DEFAULTS)
    if "schema_version" in data:
        _expect("schema_version", data["schema_version"], int)
        if data["schema_version"] != SCHEMA_VERSION:
            raise ConfigError(f"schema_version: unsupported {data['schema_version']}, this plugin reads {SCHEMA_VERSION}")

    project = _table("project", data["project"], {"pai_org", "pai_project", "linear_team", "issue_prefix"}, {"pai_org", "pai_project", "linear_team"})
    out["project"] = {k: _string(f"project.{k}", v) for k, v in project.items()}
    out["project"].setdefault("issue_prefix", out["project"]["linear_team"])
    if not re.fullmatch(r"[A-Z][A-Z0-9]*", out["project"]["issue_prefix"]):
        raise ConfigError("project.issue_prefix: must be upper-case letters and digits, like ACME")

    for name, command in _named("gates", data.get("gates", {})).items():
        if name == HOTFIX_GATE:
            out["gates"][name] = _hotfix(command)
        elif isinstance(command, list):
            if not command:
                raise ConfigError(f"gates.{name}: command list must not be empty")
            out["gates"][name] = _strings(f"gates.{name}", command, unique=False)
        else:
            out["gates"][name] = [_string(f"gates.{name}", command)]

    for name, zone in _named("zones", data.get("zones", {})).items():
        zone = _table(f"zones.{name}", zone, {"globs", "owners", "root"}, {"globs"})
        globs = _strings(f"zones.{name}.globs", zone["globs"])
        if not globs:
            raise ConfigError(f"zones.{name}.globs: must list at least one glob")
        if "root" in zone:
            _expect(f"zones.{name}.root", zone["root"], bool)
        out["zones"][name] = {"globs": globs, "owners": _strings(f"zones.{name}.owners", zone.get("owners", [])), "root": zone.get("root", False)}

    for name, machine in _named("machines", data.get("machines", {})).items():
        machine = _table(f"machines.{name}", machine, {"host", "os", "max_agents"})
        entry = {}
        for key in ("host", "os"):
            if key in machine:
                entry[key] = _string(f"machines.{name}.{key}", machine[key])
        if "max_agents" in machine:
            entry["max_agents"] = _positive(f"machines.{name}.max_agents", machine["max_agents"])
        out["machines"][name] = entry

    for name, queue in _named("queues", data.get("queues", {})).items():
        queue = _table(f"queues.{name}", queue, {"machine", "model", "limit"})
        entry = {}
        if "machine" in queue:
            entry["machine"] = _string(f"queues.{name}.machine", queue["machine"])
            if entry["machine"] not in out["machines"]:
                raise ConfigError(f"queues.{name}.machine: unknown machine {entry['machine']!r} (declare it in [machines])")
        if "model" in queue:
            entry["model"] = _choice(f"queues.{name}.model", queue["model"])
        if "limit" in queue:
            entry["limit"] = _positive(f"queues.{name}.limit", queue["limit"])
        out["queues"][name] = entry

    limits = _table("limits", data.get("limits", {}), set(DEFAULTS["limits"]))
    for key, value in limits.items():
        out["limits"][key] = _positive(f"limits.{key}", value)

    rules = _table("rules", data.get("rules", {}), set(DEFAULTS["rules"]))
    for key in ("agents_file", "push_wrapper"):
        if key in rules:
            out["rules"][key] = _string(f"rules.{key}", rules[key])
    for key in ("root_paths", "must", "never"):
        if key in rules:
            out["rules"][key] = _strings(f"rules.{key}", rules[key])

    role_zones = _table("role_zones", data.get("role_zones", {}), set(ROLES))
    for role, names in role_zones.items():
        out["role_zones"][role] = _strings(f"role_zones.{role}", names)
        for i, zone in enumerate(out["role_zones"][role]):
            if zone not in out["zones"]:
                raise ConfigError(f"role_zones.{role}[{i}]: unknown zone {zone!r} (declare it in [zones])")

    models = _table("models", data.get("models", {}), set(ROLES))
    for role, model in models.items():
        out["models"][role] = _choice(f"models.{role}", model)

    if "knowledge" in data:
        out["knowledge"] = _knowledge(data["knowledge"])
    return out


KNOWLEDGE_KEYS = {"organization", "project", "product"}


def _target(path: str, value: object, top: bool) -> dict:
    """One Knowledge target: an organization (required on the default, inherited by a stream) and exactly one of project or product."""
    table = _table(path, value, KNOWLEDGE_KEYS | ({"streams"} if top else set()))
    if top and "organization" not in table:
        raise ConfigError(f"{path}.organization: required key is missing")
    scope = [key for key in ("project", "product") if key in table]
    if len(scope) != 1:
        raise ConfigError(f"{path}: name exactly one of project or product" + (" (both given)" if scope else " (neither given)"))
    return {key: _string(f"{path}.{key}", table[key]) for key in sorted(KNOWLEDGE_KEYS & set(table))}


def _knowledge(value: object) -> dict:
    """[knowledge]: the default Pai Knowledge target plus optional [knowledge.streams.NAME] overrides."""
    out = _target("knowledge", value, True)
    streams = _named("knowledge.streams", value.get("streams", {}))  # type: ignore[attr-defined]
    out["streams"] = {name: _target(f"knowledge.streams.{name}", stream, False) for name, stream in streams.items()}
    return out


def resolve_knowledge(config: dict, stream: str | None = None) -> dict | None:
    """The Knowledge target for a stream: its override (the organization falls back to the default), else the default.

    Returns {"organization", "project" or "product", "stream"} or None when nothing is configured. A stream name with no
    override resolves to the default target; an override replaces the default's project or product as a whole.
    """
    knowledge = config.get("knowledge") or {}
    if not knowledge:
        return None
    override = knowledge.get("streams", {}).get(stream or "")
    source = override or knowledge
    scope = {key: source[key] for key in ("project", "product") if key in source}
    return {"organization": source.get("organization", knowledge["organization"]), **scope, "stream": stream if override else None}


def _hotfix(value: object) -> dict:
    """The red-release hotfix profile: active only while active_when FAILS on the release tip."""
    path = f"gates.{HOTFIX_GATE}"
    table = _table(path, value, {"active_when", "applies_to", "pre_merge", "post_merge", "revert_on_failure"},
                   {"active_when", "applies_to", "pre_merge", "post_merge"})
    pre_merge = _strings(f"{path}.pre_merge", table["pre_merge"], unique=False)
    if not pre_merge:
        raise ConfigError(f"{path}.pre_merge: command list must not be empty")
    applies_to = _string(f"{path}.applies_to", table["applies_to"])
    try:
        re.compile(applies_to)
    except re.error as error:
        raise ConfigError(f"{path}.applies_to: invalid regular expression: {error}") from None
    if "revert_on_failure" in table:
        _expect(f"{path}.revert_on_failure", table["revert_on_failure"], bool)
    return {"active_when": _string(f"{path}.active_when", table["active_when"]), "applies_to": applies_to, "pre_merge": pre_merge,
            "post_merge": _string(f"{path}.post_merge", table["post_merge"]), "revert_on_failure": table.get("revert_on_failure", True)}


def _choice(path: str, value: object) -> str:
    _string(path, value)
    if value not in MODEL_CHOICES:
        raise ConfigError(f"{path}: unknown model {value!r} (allowed: {', '.join(MODEL_CHOICES)})")
    if value == "none" and not path.endswith(".watcher"):
        raise ConfigError(f"{path}: 'none' is only allowed for the watcher, which is a script")
    return value  # type: ignore[return-value]


def load_file(path: Path) -> dict:
    """Parse and validate one config file."""
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"{path}: file not found") from None
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path}: invalid TOML: {error}") from None
    return validate(data)


def find_config(start: Path) -> Path:
    """Walk up from start to the nearest .pai-harness.toml."""
    start = Path(start).resolve()
    for directory in (start, *start.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    raise ConfigError(f"no {CONFIG_NAME} found in {start} or any parent directory")
