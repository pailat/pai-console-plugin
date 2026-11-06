#!/usr/bin/env python3
"""PreToolUse: enforce the write zone of the current role and refuse a direct git push.

Write, Edit, MultiEdit and NotebookEdit are checked by file path; Bash is checked for output redirects, tee targets and
`git push`. The zones come from .pai-harness.toml. The agent's own zones are the zone names in PAI_HARNESS_ZONES
(comma separated), else every zone that lists PAI_HARNESS_AGENT as an owner.

- A path inside the project that is outside the agent's zones is denied with the owner of the zone it falls in
  named, so the agent files a zone request. With no zone assigned, only paths inside a declared zone are denied.
- Paths outside the project root and the harness state dir are never policed (the delta marker lives there).
- `git push` is allowed only as a command that starts with the push queue wrapper: the config key rules.push_wrapper
  when the schema has it, else PAI_HARNESS_PUSH_WRAPPER. With none configured every push is refused.
- With a role set and no usable config, writes and pushes are denied (fail closed). With no role the hook does nothing.
"""
from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common as common  # noqa: E402

WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
SEPARATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", "{", "}"}
SHELLS = {"sh", "bash", "zsh", "dash"}
IGNORED_TARGETS = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def glob_regex(glob: str) -> re.Pattern:
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile(out + r"\Z")


def zone_of(relative: str, zones: dict, names: list[str] | None = None) -> str | None:
    for name in names if names is not None else zones:
        if any(glob_regex(g).match(relative) for g in zones[name]["globs"]):
            return name
    return None


def my_zones(config: dict, agent: str) -> list[str]:
    chosen = os.environ.get("PAI_HARNESS_ZONES", "").strip()
    if chosen:
        return [n for n in (part.strip() for part in chosen.split(",")) if n in config["zones"]]
    return [name for name, zone in config["zones"].items() if agent and agent in zone["owners"]]


def resolve(path: str, cwd: Path) -> Path:
    expanded = Path(os.path.expandvars(os.path.expanduser(path)))
    return Path(os.path.realpath(expanded if expanded.is_absolute() else cwd / expanded))


def zone_verdict(path: str, cwd: Path, config: dict, root: Path, state: Path | None, agent: str) -> str:
    """Return "" when the write is allowed, else the denial reason."""
    target = resolve(path, cwd)
    if state is not None and target.is_relative_to(Path(os.path.realpath(state))):
        return ""
    try:
        relative = target.relative_to(Path(os.path.realpath(root))).as_posix()
    except ValueError:
        return ""
    zones, mine = config["zones"], my_zones(config, agent)
    if mine and zone_of(relative, zones, mine):
        return ""
    owning = zone_of(relative, zones)
    if owning is None:
        if not mine:
            return ""
        return (f"Write zone: {relative} is outside your zones ({', '.join(mine)}) and no declared zone covers it. "
                "File a zone request with your lead instead of writing it.")
    owners = ", ".join(zones[owning]["owners"]) or "no owner is declared; ask your lead"
    root_note = " It is a ROOT zone: the change needs the orchestrator's ROOT go." if zones[owning]["root"] else ""
    return (f"Write zone: {relative} belongs to zone '{owning}', owned by {owners}.{root_note} "
            f"Your zones: {', '.join(mine) or 'none assigned'}. File a zone request with the owner instead of writing it.")


def strip_heredocs(command: str) -> str:
    lines, out, delimiter = command.split("\n"), [], None
    for line in lines:
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        out.append(line)
        found = HEREDOC.search(line)
        if found:
            delimiter = found.group(2)
    return "\n".join(out)


def segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(strip_heredocs(command).replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes: read what we can
        tokens = command.replace("\n", " ; ").split()
    out, current = [], []
    for token in tokens:
        if token in SEPARATORS:
            if current:
                out.append(current)
            current = []
        else:
            current.append(token)
    if current:
        out.append(current)
    return out


def is_git_push(tokens: list[str]) -> bool:
    for i, token in enumerate(tokens):
        if os.path.basename(token) != "git":
            continue
        j = i + 1
        while j < len(tokens) and tokens[j].startswith("-"):
            j += 2 if tokens[j] in GIT_OPTIONS_WITH_VALUE else 1
        return j < len(tokens) and tokens[j] == "push"
    return False


def strip_assignments(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[i]):
        i += 1
    return tokens[i:]


def expand(token: str) -> str:
    return os.path.expandvars(os.path.expanduser(token))


def through_wrapper(tokens: list[str], wrapper: str) -> bool:
    wanted = [expand(t) for t in shlex.split(wrapper)] if wrapper else []
    got = [expand(t) for t in strip_assignments(tokens)]
    return bool(wanted) and got[: len(wanted)] == wanted


def analyze(command: str, wrapper: str, depth: int = 0) -> tuple[list[str], bool]:
    """Return (write targets, whether a direct git push was found)."""
    targets, pushed = [], False
    for tokens in segments(command):
        for i, token in enumerate(tokens):
            if token in REDIRECTS and i + 1 < len(tokens) and not tokens[i + 1].startswith("&"):
                targets.append(tokens[i + 1])
        bare = strip_assignments(tokens)
        if bare and os.path.basename(bare[0]) == "tee":
            targets += [t for t in bare[1:] if not t.startswith("-")]
        if bare and os.path.basename(bare[0]) in SHELLS and "-c" in bare and depth < 3 and bare.index("-c") + 1 < len(bare):
            inner_targets, inner_push = analyze(bare[bare.index("-c") + 1], wrapper, depth + 1)
            targets, pushed = targets + inner_targets, pushed or inner_push
        if is_git_push(tokens) and not through_wrapper(tokens, wrapper):
            pushed = True
    return [t for t in targets if t not in IGNORED_TARGETS and "$" not in expand(t)], pushed


def main() -> None:
    event = common.read_event()
    if not common.role():
        return
    tool, tool_input = event.get("tool_name"), event.get("tool_input") or {}
    if tool in WRITE_TOOLS:
        wrapper, command = "", ""
        direct_paths = [str(tool_input.get(WRITE_TOOLS[tool]) or "")]
        pushed = False
    elif tool == "Bash":
        command = str(tool_input.get("command") or "")
        config, _, _ = common.load(event)
        wrapper = os.environ.get("PAI_HARNESS_PUSH_WRAPPER", "").strip()
        if config and config.get("rules", {}).get("push_wrapper"):
            wrapper = str(config["rules"]["push_wrapper"])
        if config is None:
            wrapper = ""  # fail closed: without a config even a wrapper push is refused
        direct_paths, pushed = analyze(command, wrapper)
    else:
        return
    direct_paths = [p for p in direct_paths if p]
    if not direct_paths and not pushed:
        return
    config, config_path, problem = common.load(event)
    if config is None or config_path is None:
        common.deny(f"The harness config could not be loaded ({problem}); with a role set, writes and pushes are refused until it can. Ask your parent.")
        return
    if pushed:
        configured = wrapper or str(config.get("rules", {}).get("push_wrapper") or "")
        how = f"Push through the push queue wrapper ({configured})." if configured else "No push queue wrapper is configured, so ask your parent to push."
        common.deny(f"Direct git push is refused. {how}")
        return
    cwd = Path(event.get("cwd") or os.getcwd())
    state, agent = common.state_dir(config), common.agent_name(event)
    for path in direct_paths:
        reason = zone_verdict(path, cwd, config, config_path.parent, state, agent)
        if reason:
            common.deny(reason)
            return


if __name__ == "__main__":
    main()
