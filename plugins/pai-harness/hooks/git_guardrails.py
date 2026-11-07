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
FAIL CLOSED: the command word of every segment (after assignments, prefix wrappers with their option values such as `timeout 5`,
`nice -n 5`, `exec -a x`, `env -u X`, and redirections such as `2>/dev/null`) must be a plain literal word; a variable, substitution, glob,
brace or escape there is refused whatever follows. A git call that changes where config comes from (GIT_CONFIG*, GIT_DIR, HOME, XDG_CONFIG_HOME,
--git-dir, -c include.*) with a subcommand that is not a git builtin is refused (it may be an alias the hook cannot read). Unbalanced quotes,
oversize input, a missed deadline and any internal error are refused too. Known limits: code generated at run time (`python -c`, `base64 -d | sh`)
is not read.
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
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash", "fish", "csh", "tcsh", "pwsh", "powershell", "nu", "xonsh", "elvish", "rc", "mksh", "yash", "posh"}
STDIN_RUNNERS = SHELLS | {"at", "batch"}  # commands that run text read from a pipe, here-string or heredoc
MAX_COMMAND = 65536  # bytes; a longer command is refused before it is tokenized (tokenizing is slow on huge input and a hook timeout does not block)
MAX_SEPARATORS = 2000  # ; & | and newlines
PARSE_BUDGET = 2.0  # seconds for the whole static reading of one command
STRING_RUNNERS = {"ssh", "su", "runuser", "watch", "sg", "script", "tmux", "screen", "parallel"}  # commands that run a string argument as a command line
PREFIXES = {"env", "command", "exec", "nohup", "builtin", "setsid", "sudo", "doas", "nice", "timeout", "xargs", "stdbuf", "ionice", "time"}
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix", "--config-env"}
BROAD = {".", "./", ":/", ":(top)", "*", "**", "./*", ":/*", "..", "../", ".*"}


def extract_substitutions(text: str) -> tuple[str, list[str]]:
    """Replace every $(...), backtick and ${...} expansion (not inside single quotes) with a marker word and return the inner command texts,
    so the outer command is read with the expansion unreadable and every inner command is checked on its own."""
    out, inners, i, single, double = [], [], 0, False, False
    while i < len(text):
        c = text[i]
        if c == "\\" and not single and i + 1 < len(text):
            out.append(text[i:i + 2])
            i += 2
            continue
        if c == "'" and not double:  # an apostrophe inside double quotes is a plain character
            single = not single
        elif c == '"' and not single:
            double = not double
        if not single and (text.startswith("$(", i) or text.startswith("${", i) or c == "`"):
            opener, closer = ("`", "`") if c == "`" else (text[i:i + 2], ")" if text[i + 1] == "(" else "}")
            j, depth = i + len(opener), 1
            while j < len(text):
                if text[j] == "\\" and closer != ")":
                    j += 2
                    continue
                if closer != "`" and text.startswith(opener, j):
                    depth += 1
                elif text[j] == closer:
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            inner = text[i + len(opener):j]  # an unclosed expansion reads to the end of the text
            if closer != "}":
                inners.append(inner)
            out.append(SUBST_GIT if closer != "}" and re.search(r"\b(git|rm)\b", inner) else SUBST)
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out), inners


HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][\w.-]*)\1")


def strip_heredocs(command: str) -> tuple[str, list[tuple[bool, str]]]:
    """Cut the bodies of heredocs out of the command: (the command without them, [(quoted delimiter, body text)]). A heredoc with no
    terminating line is not a heredoc (nothing after it is hidden)."""
    lines, out, bodies, i = command.split("\n"), [], [], 0
    while i < len(lines):
        out.append(lines[i])
        pos = i + 1
        for found in HEREDOC.finditer(lines[i]):
            dash = found.group(0).startswith("<<-")
            end = next((k for k in range(pos, len(lines)) if (lines[k].lstrip("\t") if dash else lines[k]).rstrip("\r") == found.group(2)), None)
            if end is None:
                break
            bodies.append((bool(found.group(1)), "\n".join(lines[pos:end])))
            pos = end + 1
        i = pos
    return "\n".join(out), bodies


UNRES = re.compile(r"\$|\{[^{}\s]*(?:,|\.\.)[^{}\s]*\}")  # a variable, substitution or brace expansion: the words are built at run time
BRACE = re.compile(r"\{[^{}\s]*(?:,|\.\.)[^{}\s]*\}")
SAFE_SUBS = {"status", "diff", "log", "show", "add", "fetch", "pull", "rev-parse", "ls-files", "grep", "blame", "describe", "ls-tree", "cat-file", "show-ref",
             "shortlog", "diff-tree", "check-ignore", "merge-base", "rev-list", "name-rev", "for-each-ref", "var", "version", "help", "whatchanged"}  # unresolved words are harmless here
SEMI_SUBS = {"commit", "merge"}  # an unresolved word is fine only as the value of a message-like option
VALUE_OPTIONS = {"-m", "--message", "-F", "--file", "-C", "-c", "--author", "--date", "-t", "--template", "--cleanup", "-S", "--reuse-message", "--reedit-message"}
COMMAND_KEYS = re.compile(r"^(core\.(sshcommand|pager|editor|fsmonitor|askpass|hookspath|gitproxy)|diff\.external|credential\.helper|sequence\.editor|"
                          r"filter\..*\.(clean|smudge|process)|diff\..*\.textconv|alias\..*)$")


def brace_words(token: str, budget: list[int]) -> list[str]:
    """The words a shell makes of one token with a brace expansion ({a,b} or {1..3}); the token itself when it has none."""
    found = BRACE.search(token)
    if not found:
        return [token]
    budget[0] -= 1
    if budget[0] < 0:
        raise ValueError("brace expansion produces too many words")
    body = found.group(0)[1:-1]
    if ".." in body and "," not in body:
        a, _, b = body.partition("..")
        if a.lstrip("-").isdigit() and b.lstrip("-").isdigit():
            step = 1 if int(a) <= int(b) else -1
            options = [str(n) for n in range(int(a), int(b) + step, step)][:64]
        else:
            options = [a, b]
    else:
        options = body.split(",")
    return [w for option in options for w in brace_words(token[:found.start()] + option + token[found.end():], budget)]


def expand_braces(tokens: list[str]) -> list[str]:
    budget = [200]
    if not any(BRACE.search(t) for t in tokens):
        return tokens
    return [w for token in tokens for w in brace_words(token, budget) if w or not BRACE.search(token)]  # `{git,}` is `git`: the shell drops the empty word


REDIRECT = re.compile(r"(?:\d*|&)[<>]+[|&]?(?:\d+-?)?")  # >, >>, 2>, &>, >|, >&2, <<<, <<
LITERAL = re.compile(r"[A-Za-z0-9_@%+:,./~-]+")
LITERAL_WORDS = {"[", "[[", "]", "]]", "!", ".", ":"}
PREFIX_VALUE_OPTIONS = {"env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"}, "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-R", "-T", "-U", "--user", "--group"},
                        "doas": {"-u", "-C"}, "nice": {"-n"}, "timeout": {"-s", "-k", "--signal", "--kill-after"}, "ionice": {"-c", "-n", "-p"},
                        "xargs": {"-I", "-n", "-P", "-d", "-L", "-s", "-E", "-a"}, "stdbuf": {"-i", "-o", "-e"}, "exec": {"-a"}, "time": {"-f", "-o"}}
CONFIG_ENV = re.compile(r"(GIT_CONFIG[A-Z_0-9]*|GIT_DIR|GIT_WORK_TREE|GIT_COMMON_DIR|HOME|XDG_CONFIG_HOME)=")
BUILTINS = set("""add am apply archive bisect blame branch bundle cat-file check-attr check-ignore checkout checkout-index cherry cherry-pick clean clone column commit
commit-graph commit-tree config count-objects credential describe diff diff-files diff-index diff-tree difftool fast-export fast-import fetch filter-branch
fmt-merge-msg for-each-ref format-patch fsck gc grep gui hash-object help init interpret-trailers log ls-files ls-remote ls-tree maintenance merge merge-base
mergetool mktag mktree mv name-rev notes pack-objects pack-refs prune pull push range-diff read-tree rebase reflog remote repack replace request-pull rerere
reset restore rev-list rev-parse revert rm shortlog show show-branch show-ref sparse-checkout stash status submodule switch symbolic-ref tag unpack-file
update-index update-ref update-server-info var verify-commit verify-pack verify-tag version whatchanged worktree write-tree bugreport diagnose scalar
citool bundle-uri multi-pack-index""".split())


def command_index(tokens: list[str]) -> int | None:
    """The index of the command word of a segment, found the way the shell finds it: past assignments, keywords, redirections (with their targets)
    and prefix wrappers with their option values (`timeout 5`, `nice -n 5`, `exec -a x`, `env -u X`, `sudo -u user`); None when there is none."""
    i, n = 0, len(tokens)
    while i < n:
        t = tokens[i]
        if ASSIGNMENT.fullmatch(t) or t in KEYWORDS:
            i += 1
        elif REDIRECT.fullmatch(t):
            i += 1 if re.search(r"[0-9]-?$", t) and "&" in t else 2
        elif t.isdigit() and i + 1 < n and REDIRECT.fullmatch(tokens[i + 1]):
            i += 1
        elif os.path.basename(t) in PREFIXES:
            name, valued = os.path.basename(t), PREFIX_VALUE_OPTIONS.get(os.path.basename(t), set())
            i += 1
            while i < n and (tokens[i].startswith("-") and len(tokens[i]) > 1 or name == "env" and ASSIGNMENT.fullmatch(tokens[i])):
                i += 2 if tokens[i] in valued else 1
            if name == "timeout" and i < n and not REDIRECT.fullmatch(tokens[i]):
                i += 1  # the duration
        else:
            return i
    return None


def shell_base(token: str) -> str:
    """The shell a command word names: `pwsh.exe`, `pwsh-preview` and `bash5` all read as their base name."""
    name = re.sub(r"\.exe$", "", os.path.basename(token).lower())
    return re.sub(r"[-_.]?(preview|\d[\d.]*)$", "", name) if re.match(r"[a-z]", name) else name


def tokenize(text: str) -> list[str] | None:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def shell_script(args: list[str], name: str) -> tuple[bool, str | None]:
    """For a shell's arguments: (a -c style flag was given, the script string). The script is the first non-option word after all options
    (skipping `--`, `-o NAME`, `+o NAME`, `-O NAME`); None when a -c flag was given but no script can be found."""
    has_c, j = False, 0
    while j < len(args):
        token = args[j]
        if token == "--":
            j += 1
            break
        if token.startswith("--command="):
            return True, token.partition("=")[2]
        if token == "--command":
            return True, args[j + 1] if j + 1 < len(args) else None
        if token in {"+O", "+o"}:  # `bash +O extglob -c ...`: the option takes a name
            j += 2
            continue
        lowered = token.lower()
        letters = cluster(token) if name not in {"pwsh", "powershell"} else ("c" if lowered.startswith("-c") else "")
        if name in {"pwsh", "powershell"} and lowered.startswith("-e"):
            return True, None  # -EncodedCommand: unreadable
        if name == "fish" and token == "-C":
            letters = "c"
        if token.startswith("--") or not (token.startswith("-") or token.startswith("+")) or len(token) == 1:
            if token.startswith("--"):
                j += 2 if token in {"--rcfile", "--init-file"} else 1
                continue
            break
        has_c = has_c or "c" in letters
        j += 2 if ("o" in letters or "O" in letters) and name not in {"pwsh", "powershell"} else 1
    if not has_c:
        return False, None
    rest = args[j:]
    return True, rest[0] if rest else None


def segments(command: str) -> list[list[str]]:
    text = command.replace("\\\n", "").replace("`", " ; ").replace("\n", " ; ")
    tokens = tokenize(text)
    if tokens is None:  # unbalanced quotes: read what we can (check() refuses such a command when it names git, rm or the wrapper)
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
        self.parse_deadline = time.monotonic() + PARSE_BUDGET
        self.text, self.segments_read = "", 0
        self.config_env = False  # set once an earlier segment assigned or exported a variable that moves git's configuration
        words = wrapper_words(wrapper)
        self.wrapper_words = words
        self.wrapper_name = os.path.basename(words[-1]) if words else ""

    def tick(self) -> None:
        """Called for every segment read: one overall deadline, well under the 10 s hook timeout."""
        self.segments_read += 1
        if time.monotonic() > self.parse_deadline:
            raise TimeoutError(f"deadline exceeded after {self.segments_read} segments")

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


XARGS_GIT_SUBS = {"reset", "branch", "clean", "checkout", "restore", "stash", "rebase", "update-ref", "worktree", "push"}
CAPABLE_SUBS = XARGS_GIT_SUBS - {"push"}  # a direct push is refused whole by the push guard
SUBST = "$SUBST"  # stands for a $(...), backtick or ${...} expansion once its inner command has been checked on its own
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\+?=.*", re.S)
NOT_COMMANDS = {"git", "echo", "printf", "grep", "egrep", "fgrep", "rg", "man", "which", "type", "cat", "ls", "head", "tail", "less", "sed", "awk", "wc"}  # their arguments are text or git's own
SUBST_GIT = "$SUBSTGIT"  # the same, when the inner command text names git or rm
LOOKUP_TIMEOUT = 3  # seconds for one git call; pre_tool_use.py has a 10 s hook timeout, and a hook timeout does not block
LOOKUP_BUDGET = 3  # seconds for all git calls of one check()


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
        if directory != "\0unknown":  # the sentinel marks an unreadable --git-dir / --work-tree; it is never a path
            current = current / os.path.expanduser(directory)
    return current


def refuse(command: list[str], why: str, alternative: str) -> str:
    shown = " ".join(repr(t) if re.search(r"\s", t) else t for t in command)[:160]
    shown = shown.replace(SUBST_GIT, "$(...)").replace(SUBST, "$(...)")
    return f"git-guardrails: `{shown}` is blocked ({why}). Safe alternative: {alternative}"


PROTECTED = ("main", "staging", "production", "release/*")
GLOB = re.compile(r"[*?\[]")
UNREADABLE = re.compile(r"[$`~{]")
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
    repo_given = any(t == "--repo" or t.startswith("--repo=") for t in args)  # the remote comes from the option: every positional is a refspec
    refspecs = (plain if repo_given else plain[1:]) or ["HEAD"]
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


def git_check(tokens: list[str], ctx: Context, depth: int, inline: dict[str, str] | None = None, env_changed: bool = False) -> str:
    """tokens start at `git`. Returns the refusal text or an empty string."""
    directories, aliases, j, hooks_path = [], dict(inline or {}), 1, False
    while j < len(tokens) and tokens[j].startswith("-"):
        token = tokens[j]
        if token in {"-C"} and j + 1 < len(tokens):
            directories.append("\0unknown" if "$" in tokens[j + 1] else tokens[j + 1])
        if token.startswith("--config-env"):
            return refuse(tokens, "a git option reads configuration from an environment variable, so it cannot be read", "use plain git options")
        if "$" in token:
            return refuse(tokens, "a git option is built by a variable or substitution, so it cannot be read", "spell the option out as a literal word")
        if token == "-c" and j + 1 < len(tokens):
            key, _, value = tokens[j + 1].partition("=")
            hooks_path = hooks_path or key.lower() == "core.hookspath"
            if re.match(r"include(if)?\.", key.lower()):
                env_changed = True  # an included file can define aliases the hook cannot read
            if key.lower() != "core.hookspath" and COMMAND_KEYS.match(key.lower()) and not key.lower().startswith("alias."):
                return refuse(tokens, f"-c {key} makes git run a command the reader cannot see", "use plain git options")
            if key.lower().startswith("alias."):
                aliases[key[len("alias."):].lower()] = value
        if token.startswith("--git-dir") or token.startswith("--work-tree"):
            directories.append("\0unknown")  # an unknown location is never a throwaway
        j += 2 if token in GIT_VALUE_OPTIONS else 1
    rest = tokens[j:]
    if not rest:
        return ""
    if (env_changed or "\0unknown" in directories) and rest[0].lower() not in BUILTINS:
        return refuse(tokens, f"git {rest[0]} is not a git builtin and this command changes where git reads its configuration from (GIT_CONFIG*, GIT_DIR, HOME, XDG_CONFIG_HOME, --git-dir, -c include.*), so it may be an alias the hook cannot read",
                      "run a git builtin, or use the default configuration")
    if hooks_path and rest[0].lower() != "push":  # a push with core.hooksPath is refused with the no-verify text by pre_tool_use.py
        return refuse(tokens, "core.hooksPath overrides the git hooks", "fix what the hook reports instead of bypassing it")
    effective = effective_dir(directories, ctx)
    unknown = "\0unknown" in directories or ctx.unknown_cwd
    embedded = embedded_command(rest[0].lower(), rest[1:])
    if embedded is not None:  # `rebase --exec CMD` and `submodule foreach CMD` run a shell command line
        if depth >= 3 or UNRES.search(embedded):
            return refuse(tokens, f"git {rest[0]} runs a command that is built at run time or nested too deep, so it cannot be read", "run the command directly")
        run_at = ctx.moved(toplevel(effective) or effective)  # git runs it from the top level of the worktree (a submodule's for foreach: unknown)
        reason = check_command(embedded, run_at.moved(None) if rest[0].lower() == "submodule" else run_at, depth + 1)
        if reason:
            return reason
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
            return check_command(value[1:] + " " + shlex.join(args), ctx.moved(toplevel(effective) or effective), depth + 1)  # a shell alias runs at the top level
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


def embedded_command(sub: str, args: list[str]) -> str | None:
    """The shell command line git runs for `rebase -x/--exec CMD` and `submodule foreach CMD`; None when the subcommand has none."""
    if sub == "rebase":
        found = []
        for k, t in enumerate(args):
            if t in {"-x", "--exec"} and k + 1 < len(args):
                found.append(args[k + 1])
            elif t.startswith("--exec="):
                found.append(t.partition("=")[2])
            elif t.startswith("-x") and not t.startswith("--") and len(t) > 2:
                found.append(t[2:])
        return " ; ".join(found) if found else None
    if sub == "submodule" and "foreach" in args:
        words = [t for t in args[args.index("foreach") + 1:] if t not in {"--recursive", "-q", "--quiet"}]
        return " ".join(words)
    return None


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
    if UNRES.search(sub):
        return refuse(shown, "the git subcommand is built by a variable, substitution or brace expansion, so it cannot be read", "spell the git subcommand out")
    sub = sub.lower()
    unresolved = [k for k, t in enumerate(args) if UNRES.search(t)]
    if unresolved and sub not in SAFE_SUBS:
        value_of = lambda k: k > 0 and (args[k - 1] in VALUE_OPTIONS or args[k - 1].startswith("-") and not args[k - 1].startswith("--") and args[k - 1][-1:] in "mFCct")  # noqa: E731
        if sub not in SEMI_SUBS or any(not value_of(k) for k in unresolved):
            return refuse(shown, f"a word of git {sub} is built by a variable, substitution or brace expansion ($VAR, $(...), backticks, ${{...}}, {{a,b}}), so it cannot be read; only read-only subcommands accept one",
                          "spell the arguments out as literal words")
    letters = option_letters(args, VALUED_LETTERS.get(sub, ""))
    if sub == "config" and any(COMMAND_KEYS.match(t.lower()) or "alias." in t.lower() or "hookspath" in t.lower() for t in args):
        return refuse(shown, "git config sets an alias or core.hooksPath, which changes what later git commands do", "use plain git commands; ask your lead for configuration changes")
    if sub == "commit" and "n" in option_letters(args, "mFCct"):
        return refuse(shown, "commit -n is --no-verify and skips the git hooks", "fix what the hook reports instead of bypassing it")
    if sub in {"commit", "merge", "am", "cherry-pick", "rebase"} and any(longopt(t, "no-verify", least=5) for t in args):
        return refuse(shown, "--no-verify skips the git hooks", "fix what the hook reports instead of bypassing it")
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
    if sub == "branch" and ({"D", "f", "M", "C"} & letters or any(longopt(t, "force") for t in args)):
        return refuse(shown, "branch -D / -f deletes or moves a branch without the merged check", "git branch -d (refuses an unmerged branch), or ask your lead")
    if sub == "switch" and ("f" in letters or "C" in letters or any(longopt(t, "force", "discard-changes", "force-create") for t in args)):
        return refuse(shown, "switch -f / --discard-changes / -C discards local changes or resets a branch", "commit or stash first, then git switch <branch> (or -c for a new branch)")
    if sub == "checkout-index" and ("f" in letters or "a" in letters or any(longopt(t, "force", "all") for t in args)):
        return refuse(shown, "checkout-index -f / -a overwrites the worktree files", "git restore of one named file")
    if sub == "read-tree" and any(longopt(t, "reset") for t in args):
        return refuse(shown, "read-tree --reset overwrites the index and worktree", "git restore of one named file")
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


VALUED_LETTERS = {"clean": "e", "rebase": "XxsSC", "commit": "mFCct"}  # short options whose value is the rest of the cluster (`-enode_modules`, `-Xpatience`)


def option_letters(args: list[str], valued: str = "") -> set[str]:
    """The short-option letters of args, each cluster read up to the first option that takes a value (the value is not letters)."""
    found: set[str] = set()
    for token in args:
        for c in cluster(token):
            if c in valued:
                break
            found.add(c)
    return found


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
    if any(t.startswith("--pathspec-from-file") for t in args):
        return refuse(shown, "the pathspecs come from a file or stdin, so they cannot be read", "name the files as literal words")
    top = toplevel(effective)
    wide = [s for s in specs if broad(s) or top is not None and not s.startswith(":") and not GLOB.search(s)
            and Path(os.path.realpath(top)).is_relative_to(Path(os.path.realpath(effective / os.path.expanduser(s))))]
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
    tops = [t for t in (toplevel(ctx.cwd), toplevel(ctx.origin)) if t is not None]  # the repository the session started in counts after a `cd` too
    for target in plain:
        ctx.tick()
        if target.startswith("$") or ".git" in target and "$" in target:
            return refuse(tokens, f"the rm -r target {target.replace(SUBST_GIT, '$(...)').replace(SUBST, '$(...)')} is built by a variable or substitution, so it cannot be checked against .git",
                          "name the path to remove as a literal word")
        parts = [p for p in re.split(r"/+", target) if p]
        if parts and parts[-1] in {"*", "**"} and any(Path(os.path.realpath(top)) == Path(os.path.realpath(ctx.cwd / os.path.expanduser("/".join(parts[:-1]) or "."))) for top in tops):
            return refuse(tokens, "rm -r of everything in the top level of the repository discards the whole worktree", "remove only the named files with git rm, or ask your lead")
        on_git = ".git" in parts or any(p[:1] in {".", "[", "\\"} and any(c in p for c in "*?[") and fnmatch.fnmatchcase(".git", p) for p in parts)
        resolved = Path(os.path.realpath(ctx.cwd / os.path.expandvars(os.path.expanduser(target))))
        covers = any(Path(os.path.realpath(top)).is_relative_to(resolved) for top in tops)
        if on_git or covers:
            return refuse(tokens, "removing .git (or a directory that holds it) destroys the repository and its history", "remove only the named files with git rm, or ask your lead")
    return ""


NAME_FILTERS = {"-name": ".git", "-iname": ".git", "-path": "./.git/HEAD", "-ipath": "./.git/HEAD", "-wholename": "./.git/HEAD"}


def excludes_git(tokens: list[str]) -> bool:
    """True only when the find expression provably leaves .git alone: a literal `-name .git -prune` / `-path ./.git -prune`, or positive -name/-path patterns
    (no negation, -o or -regex) that cannot match .git or anything below it."""
    if "-prune" in tokens and any(tokens[k] in {"-name", "-path"} and tokens[k + 1].rstrip("/*") in {".git", "./.git", "*/.git"} for k in range(len(tokens) - 1)):
        return True
    if {"!", "-not", "-o", "-or", "-regex", "-iregex"} & set(tokens):
        return False
    patterns = [(tokens[k], tokens[k + 1]) for k in range(len(tokens) - 1) if tokens[k] in NAME_FILTERS]
    return bool(patterns) and not any(fnmatch.fnmatchcase(sample, pattern) or fnmatch.fnmatchcase(".git", pattern) or fnmatch.fnmatchcase("./.git", pattern)
                                      for flag, pattern in patterns for sample in [NAME_FILTERS[flag], ".git/HEAD"])


def destroy_check(tokens: list[str], ctx: Context) -> str:
    """find -delete / -exec over .git or over a directory that holds it, and mv/unlink/shred/truncate/dd on a .git path."""
    name = os.path.basename(tokens[0])
    if name == "find":
        starts = []
        for t in tokens[1:]:
            if t.startswith("-") or t in {"(", "!"}:
                break
            starts.append(t)
        acts = any(t in {"-delete", "-exec", "-execdir", "-ok", "-okdir"} for t in tokens)
        top = toplevel(ctx.cwd)
        for start in starts or ["."]:
            holds = ".git" in start or "$" in start or top is not None and Path(os.path.realpath(top)).is_relative_to(Path(os.path.realpath(ctx.cwd / os.path.expanduser(start))))
            if acts and (".git" in start or UNRES.search(start) or (".git" in tokens or holds) and not excludes_git(tokens)):
                return refuse(tokens, "find -delete / -exec over .git or a directory that holds it destroys the repository", "give find a -name / -path filter that excludes .git, or name the files to remove")
        return ""
    if name in {"mv", "unlink", "shred", "truncate", "dd"} and any(re.search(r"(^|[=/])\.git(/|$)", t) for t in tokens[1:]):
        return refuse(tokens, f"{name} on a .git path damages the repository", "leave .git alone; ask your lead")
    if name in {"ln", "cp", "install", "rsync", "mv"} and ctx.wrapper_name and any(os.path.basename(t) == ctx.wrapper_name for t in tokens[1:]):
        return refuse(tokens, "a copy or link of the push queue wrapper would run under another name", "call the push queue wrapper by its configured path")
    return ""


def wrapper_words(wrapper: str) -> list[str]:
    """The configured wrapper as words; an unbalanced quote falls back to a plain split (never raises)."""
    try:
        words = shlex.split(wrapper) if wrapper else []
    except ValueError:
        words = wrapper.split()
    return [os.path.expandvars(os.path.expanduser(w)) for w in words]  # `$ROOT/queue-push.sh` and `~/queue-push.sh`: the shell expands them too


def same_file(token: str, wanted: str, cwd: Path) -> bool:
    """True when two spellings (`scripts/q.sh`, `./scripts/q.sh`, an absolute path) name the same file, relative to the cwd or its git top level."""
    token, wanted = os.path.expandvars(os.path.expanduser(token)), os.path.expandvars(os.path.expanduser(wanted))
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
    if not wanted or len(tokens) < len(wanted):
        return 0
    first = os.path.expandvars(os.path.expanduser(tokens[0]))
    if os.path.basename(first) != os.path.basename(wanted[0]) or not same_file(tokens[0], wanted[0], cwd):  # cheap test first: no file system work for other words
        return 0
    return len(wanted) if [os.path.expandvars(os.path.expanduser(t)) for t in tokens[1:len(wanted)]] == wanted[1:] else 0


READONLY_GIT = {"status", "diff", "log", "show", "add", "grep", "ls-files", "blame", "rev-parse", "cat-file", "check-ignore", "fetch", "ls-tree", "describe"}
XARGS_VALUED = {"-I", "-n", "-P", "-d", "-L", "-s", "-E", "-a"}  # -i, -e and -l take an attached value only


def xargs_check(tokens: list[str], ctx: Context) -> str:
    """`xargs CMD`: stdin supplies words the command line does not show (flags included), so only CMD names that cannot do harm run unread."""
    k = 1
    while k < len(tokens) and tokens[k].startswith("-"):
        k += 2 if tokens[k] in XARGS_VALUED else 1
    if k >= len(tokens):
        return ""
    command, base = tokens[k], shell_base(tokens[k])
    if "$" in command:
        return refuse(tokens, "the command xargs runs is built by a variable or substitution, so it cannot be read", "call the command by name")
    if os.path.basename(command) == "rm" and "--" in tokens[k + 1:] and not any(t.startswith("-") and t != "--" for t in tokens[k + 1:tokens.index("--", k + 1)]):
        return ""  # after `--` stdin can supply paths only, never flags
    if os.path.basename(command) == "git":
        j = k + 1
        while j < len(tokens) and tokens[j].startswith("-"):
            j += 2 if tokens[j] in GIT_VALUE_OPTIONS else 1
        sub = tokens[j].lower() if j < len(tokens) else ""
        if sub not in READONLY_GIT:
            return refuse(tokens, f"xargs feeds git {sub or '<subcommand>'} words from stdin that cannot be read", f"run git {sub or '<subcommand>'} directly with literal arguments")
    elif base in STDIN_RUNNERS or os.path.basename(command) in {"rm", "eval", "env", "sudo", "doas", "command", "exec", "find", "mv", "dd", "shred", "truncate", "unlink"} or matches_wrapper(tokens[k:], ctx.wrapper, ctx.cwd):
        return refuse(tokens, f"xargs feeds {os.path.basename(command)} words from stdin that cannot be read (flags, paths or a refspec may arrive there)", "run the command directly with literal arguments")
    return ""


def split_string(args: list[str]) -> str | None:
    """The command text of `env -S X`, `--split-string X`, `--split-string=X`, `-SX` and clusters such as `-iSX`; None when env has no such option."""
    for k, token in enumerate(args):
        if token.startswith("--split-string="):
            return token.partition("=")[2]
        if token == "--split-string":
            return args[k + 1] if k + 1 < len(args) else ""
        if token.startswith("-") and not token.startswith("--") and "S" in token:
            rest = token[token.index("S") + 1:]
            return rest if rest else (args[k + 1] if k + 1 < len(args) else "")
    return None


def segment_check(tokens: list[str], ctx: Context, depth: int) -> str:
    original = tokens
    try:
        tokens = expand_braces(tokens)  # `git reset --har{d,}` is `git reset --hard --har` once the shell has run
    except ValueError:
        return refuse(tokens[:6], "a brace expansion produces too many words to read", "write the words out")
    if tokens is not original and any(os.path.basename(t) == "git" for t in tokens) and any(t.lower() == "push" for t in tokens):
        return refuse(original[:8], "a git push whose words are built by a brace expansion cannot be read", "write the push out as literal words, through the push queue wrapper")
    at = command_index(tokens)
    if at is not None and tokens[at] not in LITERAL_WORDS and not LITERAL.fullmatch(tokens[at]):
        shown = tokens[at].replace(SUBST_GIT, "$(...)").replace(SUBST, "$(...)")
        return refuse(tokens[at:at + 4], f"the command name {shown!r} is built by a variable, substitution, glob, brace or escape, so it cannot be read",
                      "call the command by its literal name")
    lead = True  # still in the prefix zone: assignments, prefix commands, options, redirections
    command_word = next((os.path.basename(t) for t in tokens if not (shell_base(t) in PREFIXES or t.startswith("-") or ASSIGNMENT.fullmatch(t) or t in KEYWORDS)), "")
    names = ["git", "rm", *([ctx.wrapper_name] if ctx.wrapper_name else [])]
    for i, token in enumerate(tokens):
        ctx.tick()  # one deadline for everything, checked for every word: a long segment cannot outrun it
        base = os.path.basename(token)
        shell = shell_base(token)
        globbed = re.search(r"[*?\[]", token) and token not in {"[", "[["} and not ASSIGNMENT.fullmatch(token)
        if globbed and (lead or token.startswith(("/", "./", "../", "~")) and any(fnmatch.fnmatchcase(n, base) and re.search(r"[^*?\[\]!]", base) for n in names)):
            # the shell replaces a glob in a command name by the files it matches; the guard does not walk the file system (a deep glob outruns the hook timeout)
            return refuse(tokens[i:i + 4], "a command name built by a glob (* ? [ ]) cannot be read", "call the command by its literal name")
        taken = matches_wrapper(tokens[i:i + len(ctx.wrapper_words)], ctx.wrapper, ctx.cwd) if ctx.wrapper_words else 0  # a short slice: no copy of the rest
        if taken:
            reason = push_check(tokens[i + taken:], tokens[i:], ctx)
            if reason:
                return reason
        if base == "git":
            reason = git_check(tokens[i:], ctx, depth, env_changed=ctx.config_env or any(CONFIG_ENV.match(t) for t in tokens[:i]))
        elif base == "rm" and command_word not in NOT_COMMANDS:  # `git rm -r .` and `echo rm -r .` do not run rm
            reason = rm_check(tokens[i:], ctx)
        elif base in {"find", "mv", "unlink", "shred", "truncate", "dd", "ln", "cp", "install", "rsync"} and (reason := destroy_check(tokens[i:], ctx)):
            pass
        elif lead and token == SUBST_GIT:  # the command name is built by a substitution that names git or rm
            reason = refuse(tokens[i:], "the command name is built by a substitution that resolves to git or rm", "call git or rm by name")
        elif lead and re.search(r"\$", token) and not ASSIGNMENT.fullmatch(token) and not taken:  # a command name built from a variable: read the rest as git or rm
            reason = git_check(["git", *tokens[i + 1:]], ctx, depth) or rm_check(["rm", *tokens[i + 1:]], ctx)
            if not reason and (re.search(r"git|rm", token) or ctx.wrapper_name and ctx.wrapper_name in ctx.text or re.search(r"\b(git|rm)\b", ctx.text)):
                reason = refuse(tokens[i:], "the command name is built by a variable or substitution in a command that uses git, rm or the push wrapper, so it cannot be read", "call the command by name")
        elif base == "xargs":
            reason = xargs_check(tokens[i:], ctx)
        elif base in {"sudo", "doas"} and depth < 3 and any(t.startswith("-") and {"s", "i"} & set(cluster(t)) for t in tokens[i + 1:]):
            reason = check_command(" ".join(tokens[i + 1:]), ctx, depth + 1)
        elif base == "alias" and any(re.search(r"=.*\b(git|rm)\b", t) for t in tokens[i + 1:]):
            reason = refuse(tokens[i:], "an alias for git or rm defined in the same command hides what runs next", "call git or rm by name")
        elif shell in SHELLS and (found := shell_script(tokens[i + 1:], shell))[0]:
            if found[1] is None:
                reason = refuse(tokens[i:], "the script of the shell -c cannot be found", "put the command in the shell script string as one plain word")
            elif re.match(r"\s*\$", found[1]):
                reason = refuse(tokens[i:], "the script of the shell -c is built by a variable or substitution, so it cannot be read", "put the command in the shell script string as literal words")
            elif depth >= 3:
                reason = refuse(tokens[i:], "shells nested more than three deep cannot be read", "run the git command directly")
            else:
                reason = check_command(found[1], ctx, depth + 1)
        elif depth < 3 and (base == "eval" or shell_base(token) in STRING_RUNNERS):
            reason = check_command(" ".join(tokens[i + 1:]), ctx, depth + 1) or next(
                (r for t in tokens[i + 1:] if " " in t for r in [check_command(t, ctx, depth + 1)] if r), "")
        elif base == "env" and (split := split_string(tokens[i + 1:])) is not None:
            reason = check_command(split, ctx, depth + 1) if split and depth < 3 else refuse(tokens[i:], "env --split-string builds a command that cannot be read", "call the command directly")
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
    ctx.tick()
    command, inners = extract_substitutions(command)
    if inners and depth >= 4:
        return refuse(["<command>"], "substitutions nested too deep cannot be read", "run the git command directly")
    for inner in inners:
        reason = check_command(inner, ctx, depth + 1)
        if reason:
            return reason
    for tokens in segments(command):
        ctx.tick()
        reason = segment_check(tokens, ctx, depth)
        if reason:
            return reason
        if any(CONFIG_ENV.match(t) for t in tokens):
            ctx.config_env = True
        is_cd, target = cd_target(tokens)  # later segments run where this one went (a conservative reading of subshells and `||`)
        if is_cd:
            ctx = ctx.moved(None if target is None else Path(os.path.realpath(ctx.cwd / os.path.expanduser(target))))
    return ""


def check(command: str, wrapper: str, cwd: Path) -> str:
    """Return the refusal text for a dangerous command, else an empty string. Anything the reader cannot resolve to literal words is refused with
    a reason that names it."""
    if len(command) > MAX_COMMAND or len(re.findall(r"[;&|\n]", command)) > MAX_SEPARATORS:
        return refuse(["<command>"], f"the command is too large to check ({len(command)} bytes, over {MAX_COMMAND} bytes or {MAX_SEPARATORS} separators)", "split it into smaller commands")
    ctx = Context(cwd, wrapper, toplevel(cwd))
    code, bodies = strip_heredocs(command)
    ctx.text = code
    name = ctx.wrapper_name
    mentions = bool(re.search(r"\b(git|rm|xargs|eval|find|mv|unlink|shred|truncate|dd)\b", code) or name and name in code)
    if mentions and re.search(r"\$['\"]", code):
        return refuse(["<command>"], "a $'...' or $\"...\" word (ANSI-C or locale quoting) hides what a git, rm or wrapper command receives", "use plain quotes")
    if mentions and tokenize(extract_substitutions(code)[0].replace("`", " ; ").replace("\\\n", "")) is None:
        return refuse(["<command>"], "the command has an unmatched quote, so its words cannot be read", "close the quote")
    if (mentions or "GIT_CONFIG" in code) and re.search(r"\bGIT_CONFIG_(COUNT|KEY_|VALUE_|PARAMETERS)|\bGIT_CONFIG\b", code):
        return refuse(["<command>"], "GIT_CONFIG_* environment variables set git configuration (aliases, core.hooksPath) the reader cannot see", "use plain git commands")
    reason = check_command(code, ctx)
    if reason:
        return reason
    for quoted, body in bodies:  # an unquoted heredoc body is expanded: its $(...) and backticks run
        if not quoted:
            for inner in extract_substitutions(body)[1]:
                reason = check_command(inner, ctx, 1)
                if reason:
                    return reason
    fed = re.search(r"\||<", code) is not None or bool(bodies)
    for tokens in segments(code):  # a shell (or at/batch) that reads its script from a pipe, here-string, heredoc or file redirect
        k = next((i for i, t in enumerate(tokens) if shell_base(t) in STDIN_RUNNERS), None)
        if fed and k is not None and not shell_script(tokens[k + 1:], shell_base(tokens[k]))[0] and (shell_base(tokens[k]) in {"at", "batch"} or not script_argument(tokens[k + 1:])):
            if re.search(r"\b(git|rm)\b", command) or name and name in command:
                return refuse(["<command that feeds a shell>"], f"a {shell_base(tokens[k])} script fed by a pipe, here-string or heredoc that mentions git, rm or the push wrapper cannot be read",
                              "run the git command directly, or call the push queue wrapper without a pipe")
    if name and re.search(re.escape(name) + r"[^;&|\n]*(\$\(|`|\$\{)", code):
        return refuse(["<wrapper call with a substitution>"], "a substitution can build the refspec at run time", "name the feature branch as a literal branch name")
    return ""


def script_argument(args: list[str]) -> bool:
    """True when a shell's arguments name a script file (a non-option word that is not part of a redirection)."""
    skip = False
    for n, t in enumerate(args):
        if skip:
            skip = False
        elif t.isdigit() and n + 1 < len(args) and re.fullmatch(r"[<>]+&?", args[n + 1]):  # the fd of `2>&1`
            continue
        elif re.fullmatch(r"[0-9]*[<>&]+[0-9]*", t):
            skip = not re.fullmatch(r"[0-9]*[<>]+&?[0-9-]+", t)  # `>&1` carries its target; `>` and `>&` take the next word
        elif not t.startswith("-") and not t.startswith("+"):
            return True
    return False


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
