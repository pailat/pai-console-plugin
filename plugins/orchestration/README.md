# pai-orchestration

A generic operating method for agents that work under a parent agent in [Herdr](https://herdr.dev): never go idle with work in flight, report to the parent named in the brief, close with a handoff, and use the orchestration-wake Herdr plugin. The skill is `orchestration`; it needs the Herdr skill.

## Claude Code

```bash
claude plugin marketplace add pailat/pai-console-plugin
claude plugin install pai-orchestration@pai-console-plugin
```

The plugin depends on the marketplace entry `herdr`, pinned to upstream `herdrdev/herdr` tag `v0.9.5` at commit `2ecf19a92fc3a7fff75b6ce3655ef04f4625ec01`, so installing it resolves and enables the Herdr skill. `pai-console` does not depend on it.

## Codex

Codex has no plugin dependencies and the `pai-console` Codex packages do not carry these skills. Install the Herdr skill globally with:

```bash
npx skills add herdrdev/herdr --skill herdr -g
```

That command does not pin a revision. To check what you installed, compare the sha256 of its `SKILL.md` with `vendor/herdr/PROVENANCE.json` in this repository (upstream `v0.9.5`); a different digest means a different upstream revision. The orchestration method itself is in `skills/orchestration/SKILL.md` of this plugin and can be copied into a Codex skills directory.

## Wake plugin (Herdr, per machine)

`herdr-plugins/orchestration-wake` is a Herdr plugin, not a Claude Code component. Install it on each machine, never over a live installation:

```bash
herdr plugin install pailat/pai-console-plugin/herdr-plugins/orchestration-wake --ref <tag>
```
