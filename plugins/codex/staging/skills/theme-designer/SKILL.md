---
name: theme-designer
description: "Propose or repair Pai organization themes through reads and at most eight preview attempts; never save or publish."
---

# Design a theme without saving

Read `../pai-console/SKILL.md`, `../theme/SKILL.md` and `../../environment.json`.
Use only this package's unique server_name connection. Only use whoami,
organization_list, organization_theme_get and organization_theme_preview.
Read user-provided brand files when needed. Never save a draft, publish, upload
logos, mutate resources, or call other MCP tools. This skill is guidance, not a
native tool sandbox. Ask the main agent to perform confirmed writes separately.
Resolve organizationId without guessing among ambiguous organizations. Start
from the existing draft or published theme; preserve logos and unrequested
settings. Build the complete light/dark theme with foreground/surface pairs,
brand charts, font, radius and shadow. Change shell only for a stated reason.
Use supplied brand colors; disclose derived colors. Preview, fix each issue at
its path and repeat until ok: true or at most 8 preview attempts total. Stop at
that limit and report remaining failures. Do not reset the attempt counter.
Return the complete theme JSON ready for organization_theme_save_draft, preview
ok and remaining contrast pairs/ratios/minimums, 3–6 lines of design decisions,
and differences against the published theme. Saving and publishing require the
main agent and the person's confirmation. Use the session's native model
(`gpt-6.1-sol` in the documented configuration).
