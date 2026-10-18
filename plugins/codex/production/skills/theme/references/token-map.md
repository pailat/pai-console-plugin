# Theme tokens and their Portal surfaces

Measured in develop Portal using Chrome (Abraxa, Ditto, Latitude.sh, 2026-10-13). Validator pairs come from `packages/contracts/src/theme/validate.ts` (`THEME_CONTRAST_PAIRS`).

## Theme keys

`organizationThemeSchema` version 1:

```json
{
  "schemaVersion": 1,
  "light": { "background": "oklch(1 0 0)", "primary": "oklch(0.32 0.03 120)", "…": "…" },
  "dark":  { "…": "…" },
  "font": "inter",
  "radius": 0.25,
  "shadow": "none",
  "shell": "sidebar",
  "logo": {
    "light": { "storageKey": "…/theme/logo-light-….svg", "contentType": "image/svg+xml", "bytes": 1834 },
    "dark": null
  }
}
```

- **Colors** (`light` and `dark`): `"#rrggbb"` or `"oklch(L C H)"`. Omitted keys use Pai defaults.
  - background, foreground, card, card-foreground, popover, popover-foreground;
  - primary, primary-foreground, secondary, secondary-foreground, muted, muted-foreground, accent, accent-foreground;
  - border, ring, brand, brand-foreground, brand-text;
  - chart-1 … chart-5;
  - sidebar, sidebar-foreground, sidebar-primary, sidebar-primary-foreground, sidebar-accent, sidebar-accent-foreground, sidebar-border, sidebar-ring.
- **`font`:** `inter` | `dm-sans` | `manrope` | `plus-jakarta-sans` | `figtree` | `source-serif-4` | `lora` | `null`.
- **`radius`:** 0–1.25 rem in 0.0625 steps, or `null` (Pai: 0.5).
- **`shadow`:** `none` | `soft` | `default` | `strong` | `null`.
- **`shell`:** the complete Portal app shell (a reUI app-shell block), or `null` for Pai's inset sidebar.

  | `shell` | Appearance |
  |---|---|
  | `sidebar` | Edge-aligned sidebar, collapses to icons; page on background without a card |
  | `floating` | Floating bordered/shadowed sidebar, collapses to icons; page without a card |
  | `header` | Full-width organization/search/user header above sidebar |
  | `dual-rail` | Area/user icon rail and a panel with organization, search, and area menu |
  | `section-tabs` | Topbar with organization, area pills, search; sidebar beneath |
  | `framed` | Area tabs above one rounded panel framing menu and page |
  | `topbar` | No sidebar: areas above area-menu tabs, full menu in a panel |
  | `icon-rail` | Narrow icon rail with names on hover; page fills remaining space |

  `organization_theme_preview` returns available `shells` (`id: null` = Pai). The token map below was measured with Pai's shell; **remeasure** frame, panel, and menu with another shell.
- **`logo.light` / `logo.dark`:** the **complete object** returned by `organization_theme_logo_confirm`, or `null`. A string yields the literal server error “se esperaba objeto, recibido texto” (intentional Spanish contract exception). Light logo keys must contain `/theme/logo-light-`, dark keys `/theme/logo-dark-`.

## Token surfaces

| Token | Surface | Pitfall |
|---|---|---|
| `sidebar` | **Outer frame**: side menu and surrounding panel area | — |
| `background` | **Inner panel** containing content | For colored base/white surfaces, put color in `sidebar`, white in `background`. Ditto initially had the inverse: cream inside, white outside |
| `accent-foreground` (**80 %** opacity) | **Inactive menu text** and search placeholder | Neither `sidebar-primary` nor `sidebar-foreground`. Brand-colored `accent-foreground` colors the entire menu |
| `sidebar-foreground` (70 %) | Group labels (Pai, Settings, Project) | Validator also measures it on the active item |
| `sidebar-accent` | Menu hover | — |
| Active menu item | Light: `var(--background)`, a panel-colored pill. Dark: **fixed `#232323`** (`--sidebar-item-active`) | Not themeable in dark mode |
| Input background (`--field`) | Light: `var(--background)`. Dark: **fixed `#161616`** | Not themeable. Clashes with tinted dark palettes (green, olive, navy); fits neutrals |
| `muted` | Progress tracks, stats boxes (sometimes 60 % opacity), table headers | Almost invisible in light mode (see control below) |
| `primary` / `primary-foreground` | Primary button and active-item icon | `primary` must also work as **text** on `background` and `card` |
| `ring`, `brand-text` | Focus, links, `code-token-link` | — |
| `radius` | Buttons ≈ radius; menu items ≈ radius − 2px; inner panel ≈ 2 × radius | Measured: 0.1875rem gives 3px button, 1px menu, 7px panel; 0.25 gives 4/2/8; 0.875 gives about 12/18 |
| `shadow: "none"` | `--shadow-strength: 0` | — |
| `font` | Replaces `--font-inter` | Only the seven listed fonts |

## Required validator pairs

Both modes. Text ≥4.5:1; non-text ≥3:1.

| Text ≥4.5 | Background |
|---|---|
| foreground | background |
| card-foreground, popover-foreground | card, popover |
| primary-foreground, secondary-foreground, accent-foreground, brand-foreground | Corresponding surface |
| muted-foreground | background, card, muted, accent |
| **primary** | **background, card** |
| brand-text | background, muted |
| sidebar-foreground | sidebar and active item (`#232323` in dark) |
| sidebar-primary-foreground, sidebar-accent-foreground | Corresponding surface |

| Non-text ≥3 | Background |
|---|---|
| ring | background, card, muted |
| sidebar-ring, sidebar-primary | sidebar |
| primary | muted |
| **control** (Pai-internal: light `#8f8f8f`, dark `#6f6f6f`) | **background, card, muted** |

**Control consequence:** in light mode, `muted` cannot be darker than ≈ L 0.975, or `background` ≈ L 0.976 at chroma ~0.02. Progress tracks/stats boxes are therefore almost invisible (1.04–1.07 against white). The theme cannot fix this.

## Font equivalents that worked

| Brand | Theme |
|---|---|
| Geist | `inter` |
| Nunito | `figtree` |
| Space Grotesk | `manrope` |
| Inter | `inter` |

Disclose when no exact equivalent exists.

## Reference surfaces (contrast against white)

- shadcn neutral: muted/white ≈1.10, border/white ≈1.25.
- With cream/tinted backgrounds, increase border contrast to ≈1.35–1.4.
