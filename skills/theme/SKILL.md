---
name: theme
description: "Organization branding in Pai Portal Appearance through staff-only corp organization_theme_* tools: light/dark colors, font, radius, shadow, logos, Portal shell, and AA contrast. Read/extract real product or brand tokens, convert to OKLCH, map Portal tokens, preview, save drafts, publish/revert versions, upload theme/organization logos, and verify both modes in Portal. Use for themes, branding, white-label, design tokens, typography, logos, Portal colors/layout, or matching a client's brand."
argument-hint: "[organization] [client site, app, brand, logo, or colors]"
compatibility: "Pai 0.2.5+ (MCP corp, Pai staff with organization membership)"
---

# Organization theme (Appearance)

Read shared `pai-console` first through the current client's skill mechanism. The theme brands the client's **Portal** and organization-scoped Pai views, with the same use cases/audit as Portal Appearance settings.

**References:**
- `examples/brand-theme.json`: complete validated get → preview → save_draft example.
- `references/token-map.md`: keys, actual Portal token usage, shells, validator pairs.
- `references/contrast-audit.js`: Portal contrast audit.

§4, §5, §8 derive from develop Portal measurements for Abraxa, Ditto, Latitude.sh. MCP preview checks abstract pairs; Portal is the actual verification surface.

## 1. Access and client visibility

- **Pai staff only**, corp MCP area `organization:appearance` (staff only). `organization_theme_*` are absent for clients/CRM-only users.
- **Organization membership** required (`organization_list` → `organizationId`); on `FORBIDDEN`, request membership rather than bypassing.
- Organization logo `organization_update` (§7) additionally requires owner/admin.

| State | Client-visible | Surface |
|---|---|---|
| Draft (`save_draft`) | **No** | Only `organization_theme_get` / `organization_theme_preview` |
| Published (`publish`, `revert`) | **Yes, on next load** | Entire Portal (colors/font/radius/shadow/logo/shell), `view_render` with `organizationId`, canvas-page `PortalShell` views |

`PortalShell` uses the **published theme's shell**, with no shell-selection prop. Only `organization_theme_preview` displays a draft.

## 2. Workflow

1. Discover `organization_list` → `organizationId`.
2. `organization_theme_get {organizationId}` returns published theme, draft/`issues`, last 10 versions. **Start from draft if present**, otherwise published. If neither exists, start `schemaVersion: 1`, `light: {}`, `dark: {}`, everything else `null`.
3. **Extract real-source tokens** (§4), convert to **OKLCH** (`"oklch(L C H)"`).
4. Compose **complete theme** using shadcn semantics (§5) and `references/token-map.md`. In Claude, delegate heavy preview iteration to retained `theme-designer` when available/authorized; it returns JSON. In Codex, use the generated package's theme adapter if available/authorized; otherwise iterate directly. Never assume Claude `Skill`/`Read` tools or agents exist in Codex; packaging owns those variants.
5. `organization_theme_preview {organizationId, theme}` saves nothing; returns `ok`, `issues`, prospective CSS, `shells`, and an MCP Apps component/shell-selector view where supported. Correct issues (§6) until `ok: true`. Without `theme`, previews draft, published, or Pai default. **CLI needs text fallback**; do not claim a widget rendered without client evidence.
6. Show principal colors/font/shell/differences and confirm with user. For subjective choices, offer options with preview; do not iterate blindly.
7. Upload logos (§7), place in `theme.logo`.
8. `organization_theme_save_draft {organizationId, theme}` leaves published theme unchanged. Schema/font/shell/cross-organization logo rejection: `BAD_REQUEST`, `cause.code: "THEME_REJECTED"`, `cause.issues`. Contrast issues return in `issues` but **do not block draft**.
9. **Explicit approval before publish**: `organization_theme_publish {organizationId}` publishes draft, or historical `version`. Rejects with issues for AA/schema/logo failures.
10. Verify `organization_theme_get` published version and **both modes in Portal** (§8). Conversation preview: `view_render` with `organizationId`, e.g. `PortalShell` with area/breadcrumb/user, uses published shell/colors. State any unavailable browser/desktop verification; preview is not proof of Portal rendering.

**Revert:** `organization_theme_revert {organizationId, version, publish?}` copies version to a new draft and publishes unless `publish: false`. Revalidates AA/logos; failure changes nothing. Confirm before revert, including draft-only reverts.

## 3. Theme contract

Send **complete** `theme` on every `preview`/`save_draft`, not a patch. Omitted fields disappear from draft; omitted colors fall back to Pai.

```json
{ "schemaVersion": 1,
  "light": { "primary": "#0f766e", "primary-foreground": "#ffffff", "…": "…" },
  "dark":  { "primary": "#2dd4bf", "primary-foreground": "#042f2e", "…": "…" },
  "font": "plus-jakarta-sans", "radius": 0.75, "shadow": "soft", "shell": "floating",
  "logo": { "light": null, "dark": null } }
```

- `light`/`dark` colors: only `#rrggbb` or `oklch(L C H)`, no alpha/`var()`/names. Editable keys:
  - surfaces: `background`, `foreground`, `card`, `card-foreground`, `popover`, `popover-foreground`;
  - accents: `primary`, `primary-foreground`, `secondary`, `secondary-foreground`, `muted`, `muted-foreground`, `accent`, `accent-foreground`, `border`, `ring`;
  - brand blue: `brand`, `brand-foreground`, `brand-text`;
  - charts: `chart-1` through `chart-5`;
  - sidebar: `sidebar`, `sidebar-foreground`, `sidebar-primary`, `sidebar-primary-foreground`, `sidebar-accent`, `sidebar-accent-foreground`, `sidebar-border`, `sidebar-ring`.
- **Pai retains** semantic colors (`destructive`, `success`, `warning`, `info`), field/control borders, syntax highlighting. Never attempt to change them; errors must look like errors across organizations.
- `font`: `inter` (Pai), `dm-sans`, `manrope`, `plus-jakarta-sans`, `figtree`, `source-serif-4`, `lora`, or `null`. Equivalents in token map; disclose imperfect matches.
- `radius`: 0–1.25 rem in 0.0625 (1 px) steps, or `null` (Pai 0.5). Button ≈ radius, menu item ≈ radius − 2px, panel ≈ 2 × radius; 5px button → `0.3125`.
- `shadow`: `none`, `soft`, `default`, `strong`, `null`.
- `logo.light`/`logo.dark`: **unchanged complete** `organization_theme_logo_confirm` object `{storageKey, contentType, bytes}`, or `null` (§7).

### Portal shell

`shell` chooses the Portal frame; `null` means Pai inset sidebar with page in a card. Use the authoritative `organization_theme_preview.shells` list.

| `shell` | Appearance |
|---|---|
| `sidebar` | Edge-aligned, icon-collapsible sidebar; page on background |
| `floating` | Floating bordered/shadowed, icon-collapsible sidebar |
| `header` | Full-width organization/search/user header above sidebar |
| `dual-rail` | Area icon rail and collapsible area-menu panel |
| `section-tabs` | Top area pills with area sidebar beneath |
| `framed` | Area tabs above one rounded menu/page panel |
| `topbar` | No sidebar; areas above area-menu tabs |
| `icon-rail` | Narrow icon rail; page takes remaining width |

Choose by client app/workflow, not taste. Many sections: `sidebar`/`header`; fewer sections and wide screens: `topbar`/`icon-rail`. Without a reason, keep `null`. Shell changes structure, not Portal menu sections. Token map measurements use Pai shell: **remeasure** frame/panel/menu after switching.

## 4. Token sources

Use this priority:
1. **Client dashboard/app**, if user has a session: the product system most like Portal. Latitude.sh marketing used olive/black/Space Grotesk; dashboard used neutral gray/Inter/5px radius and produced the useful theme. Read only; if login required, user signs in; **never enter credentials**.
2. Public site/login.
3. Supplied brand/logo/guide/colors. Never invent supplied brand colors; derive other tones from a single given color and disclose.

Browser inspection:
- CSS variables: `getComputedStyle(document.documentElement)`, inspect `document.styleSheets` rules.
- Computed styles of real primary button, active menu item, input, card, border. Sites may ship unused default shadcn variables; **trust computed styles**.
- Accent frequency by color occurrences; typography by rendered character counts, not CSS rule counts.

**Conversion:** CSS `lab()` is CIE Lab, D50 white. Bradford-adapt to D65 before OKLab/OKLCH or hue shifts.

## 5. shadcn practices

- OKLCH colors; brand-hued low-chroma (0.004–0.02) neutrals, like shadcn Mist/Olive.
- One primary accent; pair every `*-foreground` with its surface.
- `secondary`, `muted`, `accent` are similar subtle surfaces for hover/selection/headers.
- **Light:** pure-white `background`; tint sidebar/borders/grays. `sidebar` is **outer frame**, `background` **inner panel**. Colored frame/white surfaces means color in `sidebar`.
- **Dark:** independent tones, brighter brand/darker backgrounds, not inverted light. `card`, `popover`, `sidebar` +0.035–0.07 L above `background`; match frame/page when the real app does (Latitude).
- Inactive menu text uses `accent-foreground` at 80%; brand coloring here tints the entire menu.
- Charts: five-tone accent ramp or actual brand data palette.
- If supplied dark mode is generic (Ditto's default shadcn neutral), build a branded mode with these rules and disclose.

## 6. AA contrast (publication gate)

Server checks **light and dark**, full list in token map:
- **Text 4.5:1**: each foreground/surface (`foreground`/`background`, `card-foreground`/`card`, `primary-foreground`/`primary`, `secondary-foreground`/`secondary`, `accent-foreground`/`accent`, `brand-foreground`/`brand`…); `muted-foreground` on `background`, `card`, `muted`, **`accent`**; `primary` text on `background`/`card`; `brand-text` on `background`/`muted`; sidebar text on `sidebar`, `sidebar-primary`, `sidebar-accent`, active item (dark fixed `#232323`); Pai semantic text on `background`/`card`.
- **Non-text 3:1**: `ring` on `background`/`card`/`muted`; `sidebar-ring`/`sidebar-primary` on `sidebar`; `primary` on `muted`; internal control on `background`/`card`/`muted`.
- Borders/charts are not measured.

Issues: `{path, code: "contrast", message, ratio, required, mode, pair}`. Example: dark muted-foreground/accent 4.22:1 versus required 4.5:1, `path: "dark.accent"`. **`path` identifies the supplied key**: adjust that key's brightness (here darken `dark.accent` or omit it), preview again. Do not fix the issue by changing the other side of the pair (such as Pai's `muted-foreground`) or other untouched tokens. Tell the user which requested color changed, why (pair and ratio), and its replacement.

Typical failures:
- Light lime/yellow/cream cannot be light-mode `primary` text on background. **Invert pair:** dark primary with brand-colored foreground (Latitude olive-black/lime), or darker brand primary; use pale brand for `chart-*`/`brand`. In dark mode use bright primary/dark text.
- Dark branded `accent` breaks Pai secondary text because hover rows put `muted-foreground` on `accent`. Darken that accent until the pair passes; keep the requested color only where it is not measured against Pai text, and say so.
- Missing paired `primary-foreground` or `sidebar-foreground`.
- Internal **control** gray is Pai-owned: light `#8f8f8f`, dark `#6f6f6f`. In light, `muted` cannot be darker than ≈ L 0.975; `background` ≈ L 0.976 at chroma ~0.02. Progress tracks/stats boxes become almost invisible; **theme cannot fix this**.

## 7. Logos

**Two distinct logos; upload both:**

| | Theme | Organization |
|---|---|---|
| Surface | Portal/views, light/dark | Organization switcher avatar, General settings |
| Format | PNG/WebP/**SVG**, ≤512 KB | **PNG only**, ≤10 MB |
| Upload | `organization_theme_logo_upload_url {organizationId, variant, contentType, size}` → PUT → `organization_theme_logo_confirm {organizationId, storageKey: fileKey}` | `organization_logo_upload_url {organizationId, size}` → PUT → `organization_update {organizationId, logo: fileKey}` |
| Reference | `theme.logo.light`/`.dark`: complete `{storageKey, contentType, bytes}` | `logo`: `fileKey` string |

- Exact byte `size` (`stat -f %z` macOS, `wc -c`). Signed URL expires in **5 min**: immediately PUT exact bytes/type, e.g. `curl -X PUT -H "Content-Type: image/svg+xml" --data-binary @logo.svg "<url>"`.
- Confirm reads/type-checks/sanitizes SVG. String `storageKey` in `theme.logo` yields literal “se esperaba objeto, recibido texto”.
- **Light-mode logo is dark brand artwork**, dark-mode logo light artwork (Abraxa black/white A). Correct `variant` mandatory; light key cannot serve `logo.dark`. Ask for dark-background variant or keep `dark: null`.
- Sources: `favicon.svg`, client repo logos, inline login SVG. **Inspect before upload**: Ditto apple-touch-icon was generic/unbranded.
- For SVG→PNG or avoiding file transfer through chat, draw on browser `<canvas>` and PUT from page; storage CORS permits it.

## 8. Verify in Portal

Preview misses real opacity and near-identical surfaces. Measure Portal before publication as the existing brand baseline, then after authorized publication verify the result:
1. Open organization Portal, **reload**.
2. Run `references/contrast-audit.js` through available browser JavaScript tool/console; measure light.
3. `paiForceDark()`, wait 1–2 s, `paiContrastAudit()`; does not change user preference.
4. Inspect minimum contrast/AA failures and token-map reference surfaces: border/background ≈1.25, ≈1.35–1.4 for cream/tinted surfaces.
5. Inspect screenshots of menu, form, table, progress-bar page.

Report verification limits if browser/session unavailable; never equate MCP preview or CLI output with actual Portal verification.

## 9. Common errors

Literal server messages below remain Spanish deliberately:

| Message | Cause |
|---|---|
| `El tema no es válido; revisa los problemas indicados.` | Schema/font/shell/logo; `cause.issues` with paths |
| `Color no válido: usa #rrggbb u oklch(L C H).` | Alpha/name/`rgb()`/`var()` |
| `Ese shell no existe.` / `Esa fuente no está permitida.` | Unsupported shell/font |
| `El radio va en pasos de 1px (0.0625rem).` | Radius not multiple of 0.0625 |
| `El tema no se puede publicar: no cumple el contraste AA o tiene problemas.` | Contrast/issues: correct, save draft, publish |
| `No hay un borrador del tema que publicar.` | No draft or `version` |
| `La clave del logo … es de la otra variante.` | Wrong light/dark variant |
| `La clave del logotipo no pertenece al tema de esta organización.` | Cross-organization reference; upload here |
| `No se encontró el logotipo subido; vuelve a subirlo.` | Missing PUT/expired URL |
| `Esta versión del tema guardada ya no es válida; guarda un borrador nuevo.` | Old version fails current schema |

## 10. Conduct

Always confirm before `publish`/`revert`, including develop/staging. Finish by naming **unmatched features and their owner**: unavailable font; fixed dark active item `#232323` and field `#161616`; muted progress tracks/stats boxes; gradients/blur/glass; ghost versus solid buttons. Portal-owned limitations belong to the product team, not theme.

Never enter client credentials, publish without confirmation or Portal measurement, fabricate logo references, pass logo key strings instead of objects, send partial themes expecting merge, use pale light-mode primary, or darken light-mode muted to expose tracks (validator rejects).
