# Herdr and orchestration in pai-console

`pai-console` is the only plugin of this marketplace. Besides the Pai skills it carries three pieces for agents that work in [Herdr](https://herdr.dev), all for explicit multi-agent work and never for ordinary Pai tasks:

- **`herdr` skill.** The upstream `herdrdev/herdr` skill, vendored verbatim in `skills/herdr`. `vendor/herdr/PIN.json` holds the pin (release tag and commit), `vendor/herdr/PROVENANCE.json` the sha256 of every vendored file. Never edit the skill by hand: `python3 tools/vendor_herdr.py --tag <tag>` (or `--latest`) re-vendors it, then `python3 tools/build_codex.py`. `make check` fails when the pin, the record and the files disagree.
- **`orchestration` skill.** A generic operating method: no idle waits, the Herdr worktree rule, typed orchestrators, reporting up the chain, handoff on close. Your brief and your organization's records stay the source of truth for roles and names.
- **Wake plugin.** `herdr-plugins/orchestration-wake` is a Herdr plugin (not a Claude Code component) owned by this repository. Install it on each machine, never over a live installation:

```bash
herdr plugin install pailat/pai-console-plugin/herdr-plugins/orchestration-wake --ref <tag>
```

Example settings for remote targets (`config.env` in the plugin config directory):

```bash
PAI_WAKE_SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=8 -o IdentityAgent=none"
PAI_WAKE_REMOTE_PATH=~/bin
```

`IdentityAgent=none` skips an ssh agent that stalls a non-interactive call; drop it when the agent holds your key. Write the remote path with a tilde, never `$HOME`: `$` is rejected by the validation (only `A-Za-z0-9_./:~-` are accepted), so a `$HOME` value would be ignored and only logged. See `config.env.example` for all settings (`PAI_WAKE_FALLBACK`, `PAI_WAKE_OUTBOX`, `PAI_WAKE_HOSTS`, `PAI_WAKE_SSH_OPTS`, `PAI_WAKE_REMOTE_PATH`, `PAI_WAKE_MIN_INTERVAL`, `PAI_WAKE_MAX_PER_HOUR`).

## Release watch

`.github/workflows/herdr-release-watch.yml` runs daily. When upstream has a new release it runs `tools/vendor_herdr.py --latest`, regenerates the Codex packages and opens a pull request (a draft when `make check` fails). It never edits the skill by hand and never merges. It uses only `contents: write` and `pull-requests: write`, and its one third-party action is pinned by commit. The repository setting "Allow GitHub Actions to create and approve pull requests" (Settings > Actions > General) must be on, and only a repository admin can enable it. Until it is, the pull request step fails the job visibly with an error that names the setting (the vendoring branch is already pushed), never silently. Before merging such a pull request, review the upstream change and bump the `pai-console` version so installed copies update.

## Codex

The Codex packages carry both skills too (generated from the shared skills), with `allow_implicit_invocation: false` so they are used only when asked for explicitly.

## Upgrading from the former plugins

Earlier drafts shipped `pai-orchestration` and a separate `herdr` marketplace entry. They are gone: the marketplace maps both names to `null` in `renames` and sets `forceRemoveDeletedPlugins`, so Claude Code drops their settings keys and uninstalls the copies at the next session start (marketplace-reference "Top-level fields"; host-marketplace "Rename or remove a plugin"). `pai-console` has no `dependencies`.
