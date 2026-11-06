"""git-guardrails: refuse destructive git commands in a Bash tool call. Stdlib only.

pre_tool_use.py calls `deny_dangerous` once for every Bash command of a role-bearing agent. A PreToolUse deny holds in
bypass-permissions mode too (expected: the harness runs the hook before any permission decision; verified here only with simulated hook runs
whose permission_mode is bypassPermissions, not against an installed client). A crash of the hook is non-blocking in every mode, so deny_dangerous
denies on any internal error instead of raising.

BLOCKED (each block names the command and the safe alternative):
- a push to main, staging, production or release/* through the wrapper (`wrapper origin main` and `wrapper git push origin main`);
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

import copy
import fnmatch
import os
import time
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
    """One check() call. `cwd` follows `cd` from segment to segment; `unknown_cwd` is set when a cd target cannot be read statically.
    `branches` and `aliases` cache the git subprocess results for the whole call, and `deadline` bounds them: after it every lookup fails (and so denies)."""

    def __init__(self, cwd: Path, wrapper: str, owned: Path | None) -> None:
        self.cwd, self.wrapper, self.owned = cwd, wrapper, owned
        self.origin, self.unknown_cwd = cwd, False
        self.branches: dict[str, str | None] = {}
        self.aliases: dict[str, dict[str, str] | None] = {}
        self.deadline = time.monotonic() + LOOKUP_BUDGET

    def moved(self, cwd: Path | None) -> "Context":
        other = copy.copy(self)  # shares the caches and the deadline
        if cwd is None:
            other.unknown_cwd = True
        else:
            other.cwd = cwd
        return other

    def git(self, args: list[str], directory: Path) -> "subprocess.CompletedProcess | None":
        """Run git once; None when git cannot answer in time (a timeout must deny, never allow)."""
        left = self.deadline - time.monotonic()
        if left <= 0 or not directory.is_dir():
            return None
        try:
            return run_process(["git", *args], cwd=directory, capture_output=True, text=True, timeout=min(left, LOOKUP_TIMEOUT))
        except (OSError, subprocess.SubprocessError):
            return None


LOOKUP_TIMEOUT = 3  # seconds for one git call; pre_tool_use.py has a 10 s hook timeout, and a hook timeout does not block
LOOKUP_BUDGET = 5  # seconds for all git calls of one check()


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
GLOB = re.compile(r"[*?\[]")
UNREADABLE = re.compile(r"[$`~]")
MISSING = "\0missing"  # current_branch: the directory does not exist (yet)


def protected_patterns() -> tuple[str, ...]:
    """PAI_HARNESS_PROTECTED_BRANCHES (comma or colon separated globs) replaces the default list; an unset, empty or separator-only value keeps the default."""
    found = tuple(p.strip() for p in re.split(r"[,:]", os.environ.get("PAI_HARNESS_PROTECTED_BRANCHES", "")) if p.strip())
    return found or PROTECTED


def current_branch(directory: Path, ctx: Context) -> str | None:
    """The branch HEAD names in directory ("" for a detached HEAD); None when it cannot be told (timeout, not a repository). Cached per check()."""
    key = os.path.realpath(directory)
    if not directory.is_dir():
        return MISSING
    if key not in ctx.branches:
        done = ctx.git(["symbolic-ref", "--short", "-q", "HEAD"], directory)
        ctx.branches[key] = None if done is None or done.returncode not in (0, 1) else done.stdout.strip()
    return ctx.branches[key]


def push_check(args: list[str], shown: list[str], ctx: Context) -> str:
    for token in args:
        letters = cluster(token)
        forced = longopt(token, "force", "force-with-lease", "delete", "mirror", "prune") or "f" in letters or "d" in letters
        if forced or (token.startswith("+") and len(token) > 1) or token.startswith(":") or ":+" in token:
            return refuse(shown, "force, delete, mirror and prune pushes rewrite or remove remote history",
                          "push the feature branch normally through the push queue wrapper; for a rewritten branch or a remote branch deletion, ask your lead")
        if longopt(token, "all", "branches", least=4):
            return refuse(shown, "--all / --branches pushes every local branch, protected ones included", "name the feature branch to push")
    directories = []
    if args and os.path.basename(args[0]) == "git":  # the wrapper may be called as `wrapper git push ...`: read the push after the git options
        j = 1
        while j < len(args) and args[j].startswith("-"):
            if args[j] == "-C" and j + 1 < len(args):
                directories.append(args[j + 1])
            if args[j].startswith("--git-dir") or args[j].startswith("--work-tree"):
                directories.append("\0unknown")
            j += 2 if args[j] in GIT_VALUE_OPTIONS else 1
        if j < len(args) and args[j] != "push":  # `wrapper git status`: not a push, so no destination to check
            return ""
        args = args[j + 1:]
    _, plain = positionals(args, {"-o", "--push-option", "--repo", "--receive-pack", "--exec", "-c"})
    refspecs = plain[1:] or ["HEAD"]
    patterns = protected_patterns()
    for spec in refspecs:
        destination = spec.rpartition(":")[2]
        destination = destination.removeprefix("refs/heads/") if destination.startswith("refs/heads/") else destination.removeprefix("heads/")  # git resolves `heads/x` to refs/heads/x
        if UNREADABLE.search(destination):  # the shell or git expands it at run time: it cannot be read statically
            return refuse(shown, f"the refspec {destination} is built at run time", "name the feature branch as a literal branch name")
        if GLOB.search(destination):  # a pattern can update any head, protected ones included
            return refuse(shown, f"the pattern {destination} can update protected branches", "name the feature branch to push")
        if destination in {"HEAD", "@"}:  # `@` is an alias of HEAD: the branch the working directory is on
            if "\0unknown" in directories or ctx.unknown_cwd and not any(os.path.isabs(d) for d in directories):
                return refuse(shown, "the directory the push runs in cannot be read, so HEAD cannot be resolved", "push a named feature branch")
            where = [effective_dir(directories, ctx)]
            if not directories and ctx.cwd != ctx.origin:  # a `cd` inside a subshell does not carry over: check where the session started too
                where.append(ctx.origin)
            names = [current_branch(d, ctx) for d in where]
            if MISSING in names:
                return refuse(shown, "the directory the push runs in does not exist at this point, so HEAD cannot be resolved", "push a named feature branch from an existing directory")
            if None in names:
                return refuse(shown, "the current branch could not be read in time, so HEAD cannot be resolved", "push a named feature branch")
            if "" in names:
                return refuse(shown, "HEAD is detached, so it names no branch", "push a named feature branch")
            destination = next((n for n in names if any(fnmatch.fnmatchcase(n, p) for p in patterns)), names[0])
        if any(fnmatch.fnmatchcase(destination, p) or fnmatch.fnmatchcase(p, destination) for p in patterns):
            return refuse(shown, f"a push to the protected branch {destination}", "push a feature branch and open a pull request; the merge is done by the orchestrator")
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
    unknown = "\0unknown" in directories or ctx.unknown_cwd
    reason = subcommand_check(rest[0], rest[1:], tokens, ctx, effective, unknown)
    if reason or depth >= 3:
        return reason
    name, args, seen = rest[0].lower(), rest[1:], set()
    configured = config_aliases(effective, ctx)
    if configured is None:
        return refuse(tokens, "the git aliases could not be read in time", "retry the command; spell the git command out without an alias")
    known = {**configured, **aliases}
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
        reason = subcommand_check(name, args, ["git", name, *args], ctx, effective, unknown)
        if reason:
            return reason
    return ""


def config_aliases(directory: Path, ctx: Context) -> dict[str, str] | None:
    """The aliases git config knows in directory (cached per check()); None when git cannot answer in time."""
    key = os.path.realpath(directory)
    if key not in ctx.aliases:
        existing = directory
        while not existing.is_dir() and existing.parent != existing:  # a directory that does not exist yet: its nearest parent holds the config
            existing = existing.parent
        done = ctx.git(["config", "--get-regexp", r"^alias\."], existing)
        if done is None or done.returncode not in (0, 1):  # 1 means "no alias set"
            ctx.aliases[key] = None
        else:
            found: dict[str, str] = {}
            for line in done.stdout.splitlines():
                name, _, value = line.partition(" ")
                found[name[len("alias."):].lower()] = value
            ctx.aliases[key] = found
    return ctx.aliases[key]


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
    if sub == "switch" and ("f" in letters or "C" in letters or any(longopt(t, "force", "discard-changes", "force-create") for t in args)):
        return refuse(shown, "switch -f / --discard-changes / -C discards local changes or resets a branch", "commit or stash first, then git switch <branch> (or -c for a new branch)")
    if sub == "filter-branch":
        return refuse(shown, "filter-branch rewrites the history of every ref it touches", "ask your lead; a rewrite needs an explicit decision")
    if sub == "reflog" and plain and plain[0] in {"expire", "delete"}:
        return refuse(shown, "reflog expire / delete removes the only record that can recover lost commits", "git reflog (read only), and leave the entries in place")
    if sub == "gc" and any(t.split("=", 1)[0] == "--prune" and t.partition("=")[2] in {"now", "all"} for t in args):
        return refuse(shown, "gc --prune=now deletes unreachable objects immediately", "git gc (default grace period), or ask your lead")
    if sub == "tag" and ("d" in letters or any(longopt(t, "delete") for t in args)):
        return refuse(shown, "tag -d deletes a tag", "leave the tag in place, or ask your lead")
    if sub == "remote" and plain and plain[0] in {"rm", "remove"}:
        return refuse(shown, "remote rm removes the remote and its tracking branches", "ask your lead")
    if sub == "stash" and plain and plain[0] in {"drop", "clear"}:
        return refuse(shown, "stash drop / clear loses saved work", "git stash list and git stash apply, and leave the entry in place")
    if sub == "rebase" and ("i" in letters or any(longopt(t, "interactive") for t in args)):
        return refuse(shown, "an interactive rebase needs an editor and rewrites history", "a plain git rebase <base>, or a new commit on top")
    if sub == "update-ref" and ("d" in letters or any(longopt(t, "delete") for t in args)):
        return refuse(shown, "update-ref -d deletes a ref with no check", "git branch -d for a merged branch, or ask your lead")
    if sub == "worktree" and plain and plain[0] == "remove" and ("f" in letters or any(longopt(t, "force") for t in args)):
        return refuse(shown, "worktree remove --force deletes a worktree with uncommitted work", "git worktree remove (refuses a dirty worktree), after committing or stashing")
    if sub == "checkout":
        if "B" in letters:
            return refuse(shown, "checkout -B resets an existing branch like branch -f", "git switch -c <new-branch>")
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
        on_git = ".git" in parts or any(p[:1] in {".", "[", "\\"} and any(c in p for c in "*?[") and fnmatch.fnmatchcase(".git", p) for p in parts)
        resolved = Path(os.path.realpath(ctx.cwd / os.path.expandvars(os.path.expanduser(target))))
        covers = top is not None and Path(os.path.realpath(top)).is_relative_to(resolved)
        if on_git or covers:
            return refuse(tokens, "removing .git (or a directory that holds it) destroys the repository and its history", "remove only the named files with git rm, or ask your lead")
    return ""


def wrapper_words(wrapper: str) -> list[str]:
    """The configured wrapper as words; an unbalanced quote falls back to a plain split (never raises)."""
    try:
        return shlex.split(wrapper) if wrapper else []
    except ValueError:
        return wrapper.split()


def same_file(token: str, wanted: str, cwd: Path) -> bool:
    """True when two spellings (`scripts/q.sh`, `./scripts/q.sh`, an absolute path) name the same file, relative to the cwd or its git top level."""
    token, wanted = os.path.expanduser(token), os.path.expanduser(wanted)
    if token == wanted:
        return True
    if "/" not in token and "/" not in wanted:
        return False
    top = toplevel(cwd) or cwd
    seen = Path(os.path.realpath(cwd / token))
    return any(Path(os.path.realpath(base / wanted)) == seen for base in (top, cwd)) and "/" in token + wanted


def matches_wrapper(tokens: list[str], wrapper: str, cwd: Path) -> int:
    """The number of words the wrapper takes at the start of tokens (0 when tokens do not start with it). Any spelling of its path matches."""
    wanted = wrapper_words(wrapper)
    if not wanted or len(tokens) < len(wanted) or not same_file(tokens[0], wanted[0], cwd):
        return 0
    return len(wanted) if [os.path.expanduser(t) for t in tokens[1:len(wanted)]] == [os.path.expanduser(t) for t in wanted[1:]] else 0


def segment_check(tokens: list[str], ctx: Context, depth: int) -> str:
    lead = True  # still in the prefix zone: assignments, prefix commands, options, redirections
    for i, token in enumerate(tokens):
        base = os.path.basename(token)
        taken = matches_wrapper(tokens[i:], ctx.wrapper, ctx.cwd)
        if taken:
            reason = push_check(tokens[i + taken:], tokens[i:], ctx)
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


def cd_target(tokens: list[str]) -> tuple[bool, str | None]:
    """(is this segment a cd, its target; None when the target is not static: a variable, a substitution, `cd -`)."""
    words = tokens[:]
    while words and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0]) or words[0] in KEYWORDS):
        words = words[1:]
    if not words or os.path.basename(words[0]) not in {"cd", "pushd"}:
        return False, None
    args = [t for t in words[1:] if t not in {"-L", "-P", "-e", "-@", "--"}]
    if not args:
        return True, "~"
    if len(args) > 1 or args[0] == "-" or re.search(r"[$`*?\[]", args[0]) or args[0].startswith("~") and not args[0].startswith("~/") and args[0] != "~":
        return True, None
    return True, args[0]


def check_command(command: str, ctx: Context, depth: int = 0) -> str:
    for tokens in segments(command):
        reason = segment_check(tokens, ctx, depth)
        if reason:
            return reason
        is_cd, target = cd_target(tokens)  # later segments run where this one went (a conservative reading of subshells and `||`)
        if is_cd:
            ctx = ctx.moved(None if target is None else Path(os.path.realpath(ctx.cwd / os.path.expanduser(target))))
    return ""


def check(command: str, wrapper: str, cwd: Path) -> str:
    """Return the refusal text for a dangerous command, else an empty string."""
    top = toplevel(cwd)
    ctx = Context(cwd, wrapper, top)
    reason = check_command(command, ctx)
    if reason:
        return reason
    fed = re.search(r"\||<<", command) is not None
    for tokens in segments(command):  # a shell with no script and no -c that a pipe or here-string feeds: scan the whole command text
        shell = next((i for i, t in enumerate(tokens) if os.path.basename(t) in SHELLS), None)
        if fed and shell is not None and not any(cluster(t).endswith("c") for t in tokens) and all(t.startswith("-") for t in tokens[shell + 1:]):
            words = wrapper_words(wrapper)
            wrapper_name = os.path.basename(words[-1]) if words else ""
            if CRUDE.search(command) or wrapper_name and wrapper_name in command:
                return refuse(["<command that feeds a shell>"], "a shell reads a git or push command from a pipe that cannot be inspected", "run the git command directly, or call the push queue wrapper without a pipe")
    if wrapper_words(wrapper) and re.search(re.escape(os.path.basename(wrapper_words(wrapper)[-1])) + r"[^;&|\n]*(\$\(|`|\$\{)", command):
        return refuse(["<wrapper call with a substitution>"], "a substitution can build the refspec at run time", "name the feature branch as a literal branch name")
    return ""


def deny_dangerous(common, command: str, wrapper: str, cwd: Path) -> bool:
    """The single call site of pre_tool_use.py: deny and return True when the Bash command is a dangerous git command.
    Any internal error denies too: a hook that raises does not block, so a role never runs on an unguarded command."""
    try:
        reason = check(command, wrapper, cwd)
    except Exception as error:  # noqa: BLE001 - fail closed on every failure
        reason = f"git-guardrails: the command could not be checked ({type(error).__name__}: {error}). Safe alternative: split it into plain git commands or ask your lead."
    if reason:
        common.deny(reason)
    return bool(reason)
