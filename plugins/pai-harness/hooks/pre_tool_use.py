#!/usr/bin/env python3
"""PreToolUse: enforce the write zone of the current role and refuse a direct git push.

Write, Edit, MultiEdit and NotebookEdit are checked by file path; Bash is checked for output redirects, tee targets and
`git push`. The zones come from .pai-harness.toml. The agent's own zones are the zone names in PAI_HARNESS_ZONES
(comma separated), else every zone that lists PAI_HARNESS_AGENT as an owner.

- A path inside the project that is outside the agent's zones is denied with the owner of the zone it falls in
  named, so the agent files a zone request. With no zone assigned, only paths inside a declared zone are denied.
- Paths outside the project root and the harness state dir are never policed (the delta marker lives there).
- `git push` is allowed only as a command that starts with the push queue wrapper (after shell keywords such as `do` or `then`): the config key rules.push_wrapper
  when the schema has it, else PAI_HARNESS_PUSH_WRAPPER. With none configured every push is refused.
- With a role set and no usable config, writes and pushes are denied (fail closed). With no role the hook does nothing.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_common as common  # noqa: E402
from harness_lib import WRITING_ROLES  # noqa: E402

WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
SEPARATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", "{", "}"}
SHELL_KEYWORDS = {"do", "then", "else", "elif", "while", "until", "if", "!", "time"}  # may open a segment: `for i in 1 2; do CMD; done`
SHELLS = {"sh", "bash", "zsh", "dash"}
IGNORED_TARGETS = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
PREFIX_COMMANDS = {"env", "command", "exec", "nohup", "time", "builtin", "setsid", "sudo", "doas", "nice", "timeout", "xargs", "stdbuf", "ionice"}
PREFIX_VALUE_OPTIONS = {"env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"}, "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-R", "-T", "-U"},
                        "doas": {"-u", "-C"}, "nice": {"-n"}, "timeout": {"-s", "-k", "--signal", "--kill-after"}, "ionice": {"-c", "-n", "-p"},
                        "xargs": {"-I", "-n", "-P", "-d", "-L", "-s", "-E", "-a"}, "stdbuf": {"-i", "-o", "-e"}}
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


def zone_roots(config_root: Path, cwd: Path) -> list[Path]:
    """Directories the zone globs are relative to, found by comparing git toplevels (never path containment, so a worktree
    nested under the config's checkout is its own root). The config's directory when cwd is in the config's checkout;
    otherwise the same directory inside cwd's checkout first, then the config's directory so the other checkout is policed
    too. If git cannot answer for the config's directory itself, its place in the repository is taken from the nearest
    ancestor that git can answer for, so a config in a subdirectory keeps that subdirectory. Empty when no root can be derived
    (see roots_problem for why): the caller must fail closed."""
    config_root = Path(os.path.realpath(config_root))
    here_top, config_top = common.toplevel(Path(os.path.realpath(cwd))), common.toplevel(config_root)
    if here_top is None:
        return [config_root] if Path(os.path.realpath(cwd)).is_relative_to(config_root) else []
    if config_top is None:
        if not common.in_repository(config_root):
            return [here_top, config_root] if here_top != config_root else [config_root]
        config_top = next((t for t in map(common.toplevel, config_root.parents) if t is not None and config_root.is_relative_to(t)), None)
        if config_top is None:
            return []  # git fails for the config's directory and every ancestor: its place in the repository is unknown
    if here_top == config_top:
        return [config_root]
    return [here_top / config_root.relative_to(config_top), config_root]


def roots_problem(config_root: Path, cwd: Path) -> str:
    """Why zone_roots came back empty, for the denial and the Stop text."""
    if common.toplevel(Path(os.path.realpath(cwd))) is None:
        return (f"the working directory {cwd} is outside the harness config's directory ({config_root}) and is not a git work tree, "
                "so no zone can be applied")
    return f"git could not locate the harness config's directory ({config_root}) in its repository (it failed or timed out), so no zone can be applied"


def zone_root_for(target: Path, roots: list[Path]) -> Path | None:
    """The most specific root that contains target, or None when it lies in none (such paths are not policed)."""
    inside = [r for r in roots if target.is_relative_to(r)]
    return max(inside, key=lambda r: len(r.parts)) if inside else None


def sibling_root(target: Path, config_root: Path) -> tuple[Path | None, str]:
    """For a target that lies in none of the zone roots: (the root to judge it under, "") when it sits in another worktree of the
    config's repository (the toplevel of its checkout plus the config's subdirectory); (None, "") when it is outside that repository
    or outside any repository (not policed); (None, reason) when the lookup failed and the target may be in the config's repository."""
    start = common.nearest_existing_dir(target)
    top, mine = common.toplevel(start), common.toplevel(config_root)
    if top is None or mine is None:
        if (top is None and common.in_repository(start)) or (mine is None and common.in_repository(config_root)):
            return None, "its git checkout could not be determined"
        return None, ""
    other, own = common.common_dir(start), common.common_dir(config_root)
    if other is None or own is None:
        return None, "its git repository could not be determined"
    if other != own:
        return None, ""
    return top / config_root.relative_to(mine), ""


def zone_verdict(path: str, cwd: Path, config: dict, root: Path, state: Path | None, agent: str, follow: bool = True) -> str:
    """Return "" when the write is allowed, else the denial reason. follow=False judges a symlink by its own path (only its
    parent is resolved): a changed link is the agent's change, wherever it points."""
    target = resolve(path, cwd)
    if not follow:
        expanded = Path(os.path.expandvars(os.path.expanduser(path)))
        unresolved = os.path.abspath(expanded if expanded.is_absolute() else cwd / expanded)
        target = Path(os.path.realpath(os.path.dirname(unresolved))) / os.path.basename(unresolved)
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


def strip_keywords(tokens: list[str]) -> list[str]:
    """Drop leading shell keywords, so `do CMD` and `then ! CMD` are read as CMD. This only reveals the real command to every check below."""
    i = 0
    while i < len(tokens) and tokens[i] in SHELL_KEYWORDS:
        i += 1
    return tokens[i:]


def strip_assignments(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[i]):
        i += 1
    return tokens[i:]


def expand(token: str) -> str:
    return os.path.expandvars(os.path.expanduser(token))


def unwrap(tokens: list[str]) -> list[str]:
    """Drop leading VAR=value words and prefix commands (env, command, exec, nohup, sudo, ...), so the real command comes first."""
    tokens = strip_assignments(tokens)
    while tokens and os.path.basename(tokens[0]) in PREFIX_COMMANDS:
        name, i = os.path.basename(tokens[0]), 1
        valued = PREFIX_VALUE_OPTIONS.get(name, set())
        while i < len(tokens) and (tokens[i].startswith("-") or (name == "env" and "=" in tokens[i] and not tokens[i].startswith("="))):
            i += 2 if tokens[i] in valued else 1
        if name == "timeout" and i < len(tokens):
            i += 1  # the duration
        tokens = strip_assignments(tokens[i:])
    return tokens


def through_wrapper(tokens: list[str], wrapper: str) -> bool:
    wanted = [expand(t) for t in shlex.split(wrapper)] if wrapper else []
    got = [expand(t) for t in unwrap(tokens)]
    return bool(wanted) and got[: len(wanted)] == wanted


def is_no_verify(token: str) -> bool:
    """`--no-verify` or any unique abbreviation git accepts (`--no-verif`, `--no-v`)."""
    return token.startswith("--no-v") and "--no-verify".startswith(token)


def git_aliases(cwd: Path, directory: str | None, inline: dict[str, str]) -> dict[str, str]:
    """Aliases from `git config` (read in the directory the push would run in) plus those given inline with -c."""
    aliases: dict[str, str] = {}
    command = ["git"] + (["-C", directory] if directory else []) + ["config", "--get-regexp", r"^alias\."]
    try:
        done = run_process(command, cwd=cwd, capture_output=True, text=True, timeout=5)
        for line in done.stdout.splitlines():
            key, _, value = line.partition(" ")
            aliases[key[len("alias."):].lower()] = value
    except (OSError, subprocess.SubprocessError):
        pass
    return {**aliases, **inline}


class Analysis:
    def __init__(self) -> None:
        self.targets: list[str] = []
        self.pushed = False  # a git push outside the wrapper
        self.no_verify = False  # a push with --no-verify, wrapper or not

    def merge(self, other: "Analysis") -> None:
        self.targets += other.targets
        self.pushed, self.no_verify = self.pushed or other.pushed, self.no_verify or other.no_verify


def git_subcommand(tokens: list[str]) -> tuple[list[str], str | None, dict[str, str], bool]:
    """Split `git [options] SUB ARGS` (tokens start at git): (SUB and ARGS, -C directory, -c alias.X=Y pairs, hooks overridden)."""
    j, directory, inline, hooks = 1, None, {}, False
    while j < len(tokens) and tokens[j].startswith("-"):
        if tokens[j] == "-C" and j + 1 < len(tokens):
            directory = tokens[j + 1]
        if tokens[j] == "-c" and j + 1 < len(tokens):
            key, _, value = tokens[j + 1].partition("=")
            if key.lower().startswith("alias."):
                inline[key[len("alias."):].lower()] = value
            hooks = hooks or key.lower() == "core.hookspath"
        j += 2 if tokens[j] in GIT_OPTIONS_WITH_VALUE else 1
    return tokens[j:], directory, inline, hooks


def push_form(tokens: list[str], cwd: Path, wrapper: str, depth: int) -> tuple[bool, bool]:
    """Return (is a git push, is a push whose hooks are bypassed). Tokens are one command segment, prefixes already dropped."""
    if not tokens:
        return False, False
    if re.search(r"[$`]", tokens[0]):  # a command name we cannot resolve: assume the worst when push is an argument
        return "push" in tokens[1:], False
    if os.path.basename(tokens[0]) != "git":
        return False, False
    rest, directory, inline, hooks = git_subcommand(tokens)
    if not rest:
        return False, False
    aliases = git_aliases(cwd, directory, inline) if depth < 3 else inline
    name, seen, args = rest[0].lower(), set(), rest[1:]
    while name in aliases and name not in seen:
        seen.add(name)
        value = aliases[name].strip()
        if value.startswith("!"):  # a shell alias: read it as the command it runs
            inner = analyze(value[1:] + " " + shlex.join(args), wrapper, cwd, depth + 1)
            return inner.pushed, inner.no_verify
        try:
            parts = shlex.split(value)
        except ValueError:
            return False, False
        if not parts:
            return False, False
        expanded, _, more, more_hooks = git_subcommand(["git", *parts])
        hooks, inline = hooks or more_hooks, {**inline, **more}
        if not expanded:
            return False, False
        name, args = expanded[0].lower(), expanded[1:] + args
    if name != "push":
        return False, False
    return True, hooks or any(is_no_verify(t) for t in args)


def analyze(command: str, wrapper: str, cwd: Path, depth: int = 0) -> Analysis:
    """Find write targets, a direct git push (every spelling: absolute path, -C, env/command prefixes, aliases) and --no-verify."""
    found = Analysis()
    for tokens in map(strip_keywords, segments(command)):
        for i, token in enumerate(tokens):
            if token in REDIRECTS and i + 1 < len(tokens) and not tokens[i + 1].startswith("&"):
                found.targets.append(tokens[i + 1])
        bare = unwrap(tokens)
        if bare and os.path.basename(bare[0]) == "tee":
            found.targets += [t for t in bare[1:] if not t.startswith("-")]
        if bare and depth < 3:
            name = os.path.basename(bare[0])
            if name in SHELLS and "-c" in bare and bare.index("-c") + 1 < len(bare):
                found.merge(analyze(bare[bare.index("-c") + 1], wrapper, cwd, depth + 1))
            elif name == "eval":
                found.merge(analyze(" ".join(bare[1:]), wrapper, cwd, depth + 1))
        if through_wrapper(tokens, wrapper):
            found.no_verify = found.no_verify or any(is_no_verify(t) or t.lower().startswith("core.hookspath") for t in bare)
            continue
        is_push, bypass = push_form(bare, cwd, wrapper, depth)
        for i in range(1, len(bare)):  # a git behind any other command word (`wrapper git push` with no wrapper configured, `ssh host git push`)
            if not is_push and os.path.basename(bare[i]) == "git":
                is_push, bypass = push_form(bare[i:], cwd, wrapper, depth)
        found.pushed, found.no_verify = found.pushed or is_push, found.no_verify or (is_push and bypass)
    found.targets = [t for t in found.targets if t not in IGNORED_TARGETS and "$" not in expand(t)]
    return found


def main() -> None:
    event = common.read_event()
    if not common.role():
        return
    tool, tool_input = event.get("tool_name"), event.get("tool_input") or {}
    if tool in WRITE_TOOLS:
        wrapper, command = "", ""
        direct_paths = [str(tool_input.get(WRITE_TOOLS[tool]) or "")]
        pushed = no_verify = False
    elif tool == "Bash":
        command = str(tool_input.get("command") or "")
        config, _, _ = common.load(event)
        wrapper = os.environ.get("PAI_HARNESS_PUSH_WRAPPER", "").strip()
        if config and config.get("rules", {}).get("push_wrapper"):
            wrapper = str(config["rules"]["push_wrapper"])
        if config is None:
            wrapper = ""  # fail closed: without a config even a wrapper push is refused
        found = analyze(command, wrapper, Path(event.get("cwd") or os.getcwd()))
        direct_paths, pushed, no_verify = found.targets, found.pushed, found.no_verify
    else:
        return
    direct_paths = [p for p in direct_paths if p]
    if not direct_paths and not pushed and not no_verify:
        return
    config, config_path, problem = common.load(event)
    if config is None or config_path is None:
        common.deny(f"The harness config could not be loaded ({problem}); with a role set, writes and pushes are refused until it can. Ask your parent.")
        return
    if no_verify:
        common.deny("git push --no-verify (or a core.hooksPath override) is refused, even through the push queue wrapper. "
                    "Fix what the pre-push hook reports instead of bypassing it.")
        return
    if pushed:
        configured = wrapper or str(config.get("rules", {}).get("push_wrapper") or "")
        how = f"Push through the push queue wrapper ({configured})." if configured else "No push queue wrapper is configured, so ask your parent to push."
        common.deny(f"Direct git push is refused. {how}")
        return
    cwd = Path(event.get("cwd") or os.getcwd())
    state, agent = common.state_dir(config), common.agent_name(event)
    roots = zone_roots(config_path.parent, cwd)
    for path in direct_paths:
        target = resolve(path, cwd)
        if state is not None and target.is_relative_to(Path(os.path.realpath(state))):
            continue  # the delta marker and other state files are never policed, even with no root
        if not roots:
            # No root: police the config's checkout; a path under cwd could belong to an unknown checkout, so refuse it.
            # Anything else cannot land in a zone and is left alone.
            config_root = Path(os.path.realpath(config_path.parent))
            if target.is_relative_to(config_root) or target.is_relative_to(Path(os.path.realpath(cwd))):
                common.deny(f"Write zone: {target} could belong to a zone, but {roots_problem(config_root, cwd)}; the write is refused. "
                            "Start the agent inside the project checkout or set PAI_HARNESS_CONFIG to its own copy.")
                return
            continue
        root = zone_root_for(target, roots)
        if root is None:  # in none of the known roots: it may be another worktree of the same repository
            root, problem = sibling_root(target, Path(os.path.realpath(config_path.parent)))
            if problem and common.role() in WRITING_ROLES:
                common.deny(f"Write zone: {target} cannot be checked against the zones: {problem}; the write is refused.")
                return
        reason = zone_verdict(path, cwd, config, root, state, agent) if root is not None else ""
        if reason:
            common.deny(reason)
            return

if __name__ == "__main__":
    main()
