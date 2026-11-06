"""git-guardrails: refuse destructive git commands in a Bash tool call. Stdlib only.

pre_tool_use.py calls `deny_dangerous` once for every Bash command of a role-bearing agent. A PreToolUse deny holds in
bypass-permissions mode too, because the harness runs the hook before any permission decision.

BLOCKED (each block names the command and the safe alternative):
- a push to main, staging, production or release/* through the wrapper;
- git push with --force, -f, --force-with-lease, --delete, -d, --mirror, --prune, a `+ref` refspec or a `:branch` refspec,
  also through the push queue wrapper (the wrapper path is found anywhere in the command, e.g. `bash scripts/queue-push.sh`);
- git reset --hard, git clean (unless it is a dry run), git branch -D / -f, git stash drop / clear, git rebase -i,
  git update-ref -d, git worktree remove --force, git checkout -f;
- git checkout / git restore of a broad pathspec (`.`, `./`, `:/`, `*`, `..`, `-- .`) that discards the worktree changes
  (`git restore --staged .` only unstages and is allowed);
- rm -r on .git (any path with a `.git` component, a glob that can match it, or a parent of the git top level), and
  find ... -name .git with -delete / -exec.

THROWAWAY OPT-IN: PAI_HARNESS_GIT_THROWAWAY lists relative paths (separated by `,` or `:`) of the git top level the
agent works in. checkout/restore of a broad pathspec and git clean are allowed only when every target resolves inside
one of those paths; reset --hard, branch -D, force pushes and rm -rf .git are never opted in. Absolute entries, `..`,
`.git` and the top level itself are ignored.

PARSING: quoting, `git -C dir`, `-c`, `--git-dir=...`, env/sudo/command/xargs prefixes, `;` `&&` `||` `|` chains,
newlines, line continuations, backticks and `$( )`, sh/bash -c, eval, ssh/su/watch strings, git aliases (the literal
name AND its expansion are both checked, because git ignores an alias that shadows a builtin), a command name built
from a variable (`$g reset --hard`) and a shell that reads its script from a pipe (the whole command is scanned).
A command that cannot be parsed is read as best as possible, never skipped. Known limits: code generated at run time
(`python -c`, `base64 -d | sh`) is not read.
"""
from __future__ import annotations

import fnmatch
import os
import re
import shlex
import subprocess
from pathlib import Path
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname

SEPARATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", "{", "}"}
KEYWORDS = {"do", "then", "else", "elif", "while", "until", "if", "!", "time", "coproc"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash"}
STRING_RUNNERS = {"ssh", "su", "runuser", "watch", "sg", "script"}  # commands that run a string argument as a command line
PREFIXES = {"env", "command", "exec", "nohup", "builtin", "setsid", "sudo", "doas", "nice", "timeout", "xargs", "stdbuf", "ionice", "time"}
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix", "--config-env"}
BROAD = {".", "./", ":/", ":(top)", "*", "./*", ":/*", "..", "../", ".*"}
CRUDE = re.compile(r"git\b.*\b(reset\b.*--ha|clean\b|push\b.*(-\w*[fd]\b|--(f|de|mi|pr)|\s[+:])|branch\b.*-\w*[Df]|stash\s+(drop|clear)|rebase\b.*(-\w*i|--inter)"
                   r"|update-ref\b.*-\w*d|worktree\s+remove|checkout\b.*(\s\.(\s|$)|-f)|restore\b)|rm\b.*\.git\b")


def segments(command: str) -> list[list[str]]:
    text = command.replace("\\\n", "").replace("`", " ; ").replace("\n", " ; ")
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes: read what we can
        tokens = text.replace("(", " ; ").replace(")", " ; ").split()
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


def cluster(token: str) -> str:
    """The letters of a short-option cluster (`-fd` gives `fd`), else an empty string."""
    return token[1:] if token.startswith("-") and not token.startswith("--") and len(token) > 1 else ""


def longopt(token: str, *names: str, least: int = 3) -> bool:
    """True when token is `--name` or a git-accepted unique abbreviation of one of the names (`--ha`, `--forc`)."""
    head = token.split("=", 1)[0]
    return head.startswith("--") and len(head) >= least and any(("--" + name).startswith(head) for name in names)


def positionals(args: list[str], valued: set[str] = frozenset()) -> tuple[list[str], list[str]]:
    """Split args into (options, positionals); everything after `--` is positional and `--` itself goes to the options."""
    options, plain, skip, after = [], [], False, False
    for token in args:
        if skip:
            skip = False
        elif after:
            plain.append(token)
        elif token == "--":
            after = True
            options.append(token)
        elif token.startswith("-") and len(token) > 1:
            options.append(token)
            skip = token in valued
        else:
            plain.append(token)
    return options, plain


class Context:
    def __init__(self, cwd: Path, wrapper: str, owned: Path | None) -> None:
        self.cwd, self.wrapper, self.owned = cwd, wrapper, owned


def toplevel(directory: Path) -> Path | None:
    current = directory
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def throwaway_roots(top: Path | None) -> list[Path]:
    roots = []
    for entry in re.split(r"[,:]", os.environ.get("PAI_HARNESS_GIT_THROWAWAY", "")):
        entry = entry.strip()
        parts = Path(entry).parts
        if not entry or top is None or Path(entry).is_absolute() or ".." in parts or ".git" in parts or entry in {".", "./"}:
            continue
        roots.append(Path(os.path.realpath(top / entry)))
    return roots


def in_throwaway(targets: list[Path], ctx: Context, effective: Path) -> bool:
    top = toplevel(effective)
    if top is None or ctx.owned is None or Path(os.path.realpath(top)) != Path(os.path.realpath(ctx.owned)):
        return False
    roots = throwaway_roots(Path(os.path.realpath(top)))
    return bool(targets) and bool(roots) and all(any(Path(os.path.realpath(t)).is_relative_to(r) for r in roots) for t in targets)


def effective_dir(directories: list[str], ctx: Context) -> Path:
    current = ctx.cwd
    for directory in directories:
        current = current / os.path.expanduser(directory)
    return current


def refuse(command: list[str], why: str, alternative: str) -> str:
    shown = " ".join(repr(t) if re.search(r"\s", t) else t for t in command)[:160]
    return f"git-guardrails: `{shown}` is blocked ({why}). Safe alternative: {alternative}"


PROTECTED = ("main", "staging", "production", "release/*")


def current_branch(directory: Path) -> str:
    try:
        done = run_process(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=directory if directory.is_dir() else None,
                           capture_output=True, text=True, timeout=5)
        return done.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def push_check(args: list[str], shown: list[str], cwd: Path) -> str:
    for token in args:
        letters = cluster(token)
        forced = longopt(token, "force", "force-with-lease", "delete", "mirror", "prune") or "f" in letters or "d" in letters
        if forced or (token.startswith("+") and len(token) > 1) or token.startswith(":") or ":+" in token:
            return refuse(shown, "force, delete, mirror and prune pushes rewrite or remove remote history",
                          "push the feature branch normally through the push queue wrapper; for a rewritten branch or a remote branch deletion, ask your lead")
        if longopt(token, "no-verify", least=5) or token.startswith("core.hooksPath"):
            return refuse(shown, "a push that skips the pre-push hook", "fix what the pre-push hook reports instead of bypassing it")
    _, plain = positionals(args, {"-o", "--push-option", "--repo", "--receive-pack", "--exec", "-c"})
    refspecs = plain[1:]
    destinations = [spec.rpartition(":")[2] for spec in refspecs] or ["HEAD"]
    for destination, spec in zip(destinations, refspecs or ["HEAD"]):
        branch = destination.removeprefix("refs/heads/")
        if branch == "HEAD" and ":" not in spec:
            branch = current_branch(cwd)
        if any(fnmatch.fnmatchcase(branch, pattern) for pattern in PROTECTED):
            return refuse(shown, f"a push to the protected branch {branch}", "push a feature branch and open a pull request; the merge is done by the orchestrator")
    return ""


def git_check(tokens: list[str], ctx: Context, depth: int, inline: dict[str, str] | None = None) -> str:
    """tokens start at `git`. Returns the refusal text or an empty string."""
    directories, aliases, j = [], dict(inline or {}), 1
    while j < len(tokens) and tokens[j].startswith("-"):
        token = tokens[j]
        if token in {"-C"} and j + 1 < len(tokens):
            directories.append(tokens[j + 1])
        if token == "-c" and j + 1 < len(tokens):
            key, _, value = tokens[j + 1].partition("=")
            if key.lower().startswith("alias."):
                aliases[key[len("alias."):].lower()] = value
        if token.startswith("--git-dir") or token.startswith("--work-tree"):
            directories.append("\0unknown")  # an unknown location is never a throwaway
        j += 2 if token in GIT_VALUE_OPTIONS else 1
    rest = tokens[j:]
    if not rest:
        return ""
    effective = effective_dir(directories, ctx)
    reason = subcommand_check(rest[0], rest[1:], tokens, ctx, effective, "\0unknown" in directories)
    if reason or depth >= 3:
        return reason
    name, args, seen = rest[0].lower(), rest[1:], set()
    known = {**config_aliases(effective), **aliases}
    while name in known and name not in seen:  # also check the expansion: git ignores an alias that shadows a builtin
        seen.add(name)
        value = known[name].strip()
        if value.startswith("!"):
            return check_command(value[1:] + " " + shlex.join(args), ctx, depth + 1)
        try:
            parts = shlex.split(value)
        except ValueError:
            return refuse(tokens, "an alias that cannot be read", "spell the git command out without an alias")
        if not parts:
            return ""
        name, args = parts[0].lower(), parts[1:] + args
        reason = subcommand_check(name, args, ["git", name, *args], ctx, effective, "\0unknown" in directories)
        if reason:
            return reason
    return ""


def config_aliases(directory: Path) -> dict[str, str]:
    aliases: dict[str, str] = {}
    try:
        done = run_process(["git", "config", "--get-regexp", r"^alias\."], cwd=directory if directory.is_dir() else None,
                           capture_output=True, text=True, timeout=5)
        for line in done.stdout.splitlines():
            key, _, value = line.partition(" ")
            aliases[key[len("alias."):].lower()] = value
    except (OSError, subprocess.SubprocessError):
        pass
    return aliases


def subcommand_check(sub: str, args: list[str], shown: list[str], ctx: Context, effective: Path, unknown_dir: bool) -> str:
    sub = sub.lower()
    letters = {c for token in args for c in cluster(token)}
    options, plain = positionals(args)
    if sub == "push":  # a direct push is refused whole by the push guard of pre_tool_use.py; the wrapper path is checked in segment_check
        return ""
    if sub == "reset" and any(longopt(t, "hard") for t in args):
        return refuse(shown, "reset --hard throws away uncommitted work and moves the branch", "git stash, or git restore --staged <file>, or a new branch with git switch -c")
    if sub == "clean":
        if "n" in letters or any(longopt(t, "dry-run") for t in args):
            return ""
        _, paths = positionals(args, {"-e", "--exclude"})
        targets = [effective / p for p in paths] if paths else [effective]
        if not unknown_dir and in_throwaway(targets, ctx, effective):
            return ""
        return refuse(shown, "git clean deletes untracked files for good", "git clean -n to preview, then delete the named files yourself; a throwaway path needs PAI_HARNESS_GIT_THROWAWAY")
    if sub == "branch" and ("D" in letters or "f" in letters or any(longopt(t, "force") for t in args)):
        return refuse(shown, "branch -D / -f deletes or moves a branch without the merged check", "git branch -d (refuses an unmerged branch), or ask your lead")
    if sub == "stash" and plain and plain[0] in {"drop", "clear"}:
        return refuse(shown, "stash drop / clear loses saved work", "git stash list and git stash apply, and leave the entry in place")
    if sub == "rebase" and ("i" in letters or any(longopt(t, "interactive") for t in args)):
        return refuse(shown, "an interactive rebase needs an editor and rewrites history", "a plain git rebase <base>, or a new commit on top")
    if sub == "update-ref" and ("d" in letters or any(longopt(t, "delete") for t in args)):
        return refuse(shown, "update-ref -d deletes a ref with no check", "git branch -d for a merged branch, or ask your lead")
    if sub == "worktree" and plain and plain[0] == "remove" and ("f" in letters or any(longopt(t, "force") for t in args)):
        return refuse(shown, "worktree remove --force deletes a worktree with uncommitted work", "git worktree remove (refuses a dirty worktree), after committing or stashing")
    if sub == "checkout":
        if "f" in letters or any(longopt(t, "force") for t in args):
            return refuse(shown, "checkout -f discards local changes", "commit or stash first, then git switch <branch>")
        _, plain_c = positionals(args, {"-b", "-B", "--orphan", "-t", "--track", "--conflict", "--pathspec-from-file"})
        return pathspec_check(shown, args, plain_c, ctx, effective, unknown_dir, "git checkout of a broad pathspec overwrites the worktree changes")
    if sub == "restore":
        staged_only = ("S" in letters or any(longopt(t, "staged") for t in args)) and not ("W" in letters or any(longopt(t, "worktree") for t in args))
        if staged_only:
            return ""
        _, plain_r = positionals(args, {"-s", "--source", "--pathspec-from-file"})
        return pathspec_check(shown, args, plain_r, ctx, effective, unknown_dir, "git restore of a broad pathspec overwrites the worktree changes", restore=True)
    return ""


def broad(spec: str) -> bool:
    spec = spec.rstrip("/") if spec not in {"/", "./", ":/", "../"} else spec
    return spec in BROAD or spec.endswith("/.") or spec.endswith("/..") or spec.startswith(":(") or spec.startswith(":/") or spec == ":"


def pathspec_check(shown: list[str], args: list[str], plain: list[str], ctx: Context, effective: Path, unknown_dir: bool, why: str, restore: bool = False) -> str:
    if "--" in args:  # everything after -- is a path; a tree-ish may come before it
        specs = args[args.index("--") + 1:]
    elif restore:
        specs = plain
    else:  # checkout: the first positional is a branch or tree-ish, unless it is the lone broad pathspec itself
        specs = plain[1:] if len(plain) > 1 else (plain if plain and broad(plain[0]) else [])
    wide = [s for s in specs if broad(s)]
    if not wide:
        return ""
    if not unknown_dir and in_throwaway([effective / s for s in wide], ctx, effective):
        return ""
    return refuse(shown, why, "git stash, or git diff to review and restore one named file; a throwaway path needs PAI_HARNESS_GIT_THROWAWAY")


def rm_check(tokens: list[str], ctx: Context) -> str:
    options, plain = positionals(tokens[1:])
    recursive = any(longopt(t, "recursive") or {"r", "R"} & set(cluster(t)) for t in options)
    if not recursive:
        return ""
    top = toplevel(ctx.cwd)
    for target in plain:
        parts = [p for p in re.split(r"/+", target) if p]
        on_git = ".git" in parts or any(any(c in p for c in "*?[") and fnmatch.fnmatchcase(".git", p) for p in parts)
        resolved = Path(os.path.realpath(ctx.cwd / os.path.expandvars(os.path.expanduser(target))))
        covers = top is not None and Path(os.path.realpath(top)).is_relative_to(resolved)
        if on_git or covers:
            return refuse(tokens, "removing .git (or a directory that holds it) destroys the repository and its history", "remove only the named files with git rm, or ask your lead")
    return ""


def segment_check(tokens: list[str], ctx: Context, depth: int) -> str:
    wanted = [os.path.expanduser(t) for t in shlex.split(ctx.wrapper)] if ctx.wrapper else []
    lead = True  # still in the prefix zone: assignments, prefix commands, options, redirections
    for i, token in enumerate(tokens):
        base = os.path.basename(token)
        if wanted and os.path.expanduser(token) == wanted[0] and [os.path.expanduser(t) for t in tokens[i:i + len(wanted)]] == wanted:
            reason = push_check(tokens[i + len(wanted):], tokens[i:], ctx.cwd)
            if reason:
                return reason
        if base == "git":
            reason = git_check(tokens[i:], ctx, depth)
        elif base == "rm":
            reason = rm_check(tokens[i:], ctx)
        elif base == "find" and ".git" in tokens[i:] and any(t in {"-delete", "-exec", "-execdir", "-ok"} for t in tokens[i:]):
            reason = refuse(tokens[i:], "find on .git with -delete / -exec destroys the repository", "name the files to remove explicitly")
        elif lead and re.search(r"\$", token):  # a command name built from a variable: read the rest as git or rm
            reason = git_check(["git", *tokens[i + 1:]], ctx, depth) or rm_check(["rm", *tokens[i + 1:]], ctx)
        elif depth < 3 and base in SHELLS and any(cluster(t).endswith("c") for t in tokens[i + 1:]):
            index = next(k for k in range(i + 1, len(tokens)) if cluster(tokens[k]).endswith("c"))
            reason = check_command(tokens[index + 1], ctx, depth + 1) if index + 1 < len(tokens) else ""
        elif depth < 3 and base in SHELLS and not any(not t.startswith("-") for t in tokens[i + 1:]):
            reason = ""  # a shell reading its script from stdin: handled on the whole command by check()
        elif depth < 3 and (base == "eval" or base in STRING_RUNNERS):
            reason = check_command(" ".join(tokens[i + 1:]), ctx, depth + 1) or next(
                (r for t in tokens[i + 1:] if " " in t for r in [check_command(t, ctx, depth + 1)] if r), "")
        elif depth < 3 and base == "env" and any(t in {"-S", "--split-string"} for t in tokens[i + 1:]):
            k = next(k for k in range(i + 1, len(tokens)) if tokens[k] in {"-S", "--split-string"})
            reason = check_command(tokens[k + 1], ctx, depth + 1) if k + 1 < len(tokens) else ""
        else:
            reason = ""
        if reason:
            return reason
        lead = lead and (base in PREFIXES or token.startswith("-") or bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token)) or token in {">", ">>", "<"}
                         or i > 0 and tokens[i - 1] in {">", ">>", "<"} or token in KEYWORDS)
    return ""


def check_command(command: str, ctx: Context, depth: int = 0) -> str:
    for tokens in segments(command):
        reason = segment_check(tokens, ctx, depth)
        if reason:
            return reason
    return ""


def check(command: str, wrapper: str, cwd: Path) -> str:
    """Return the refusal text for a dangerous command, else an empty string."""
    top = toplevel(cwd)
    ctx = Context(cwd, wrapper, top)
    reason = check_command(command, ctx)
    if reason:
        return reason
    for tokens in segments(command):  # a shell fed from a pipe or a here-string: scan the whole command text
        if any(os.path.basename(t) in SHELLS for t in tokens) and not any(cluster(t).endswith("c") for t in tokens):
            if CRUDE.search(command):
                return refuse(["<command that feeds a shell>"], "a shell reads a git command from a pipe that cannot be inspected", "run the git command directly")
    return ""


def deny_dangerous(common, command: str, wrapper: str, cwd: Path) -> bool:
    """The single call site of pre_tool_use.py: deny and return True when the Bash command is a dangerous git command."""
    reason = check(command, wrapper, cwd)
    if reason:
        common.deny(reason)
    return bool(reason)
