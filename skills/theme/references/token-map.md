# Tokens del tema y dónde los pinta el Portal

Medido en el Portal de develop con Chrome (Abraxa, Ditto y Latitude.sh, 2026-10-13). Los pares que exige el validador salen de `packages/contracts/src/theme/validate.ts` (`THEME_CONTRAST_PAIRS`).

## Claves del tema

`organizationThemeSchema` versión 1:

```json
{
  "schemaVersion": 1,
  "light": { "background": "oklch(1 0 0)", "primary": "oklch(0.32 0.03 120)", "…": "…" },
  "dark":  { "…": "…" },
  "font": "inter",
  "radius": 0.25,
  "shadow": "none",
  "logo": {
    "light": { "storageKey": "…/theme/logo-light-….svg", "contentType": "image/svg+xml", "bytes": 1834 },
    "dark": null
  }
}
```

- **Colores** (`light` y `dark`): `"#rrggbb"` u `"oklch(L C H)"`. Una clave que no pongas queda con el valor de Pai.
  - background, foreground, card, card-foreground, popover, popover-foreground;
  - primary, primary-foreground, secondary, secondary-foreground, muted, muted-foreground, accent, accent-foreground;
  - border, ring, brand, brand-foreground, brand-text;
  - chart-1 … chart-5;
  - sidebar, sidebar-foreground, sidebar-primary, sidebar-primary-foreground, sidebar-accent, sidebar-accent-foreground, sidebar-border, sidebar-ring.
- **`font`:** `inter` | `dm-sans` | `manrope` | `plus-jakarta-sans` | `figtree` | `source-serif-4` | `lora` | `null`.
- **`radius`:** rem de 0 a 1.25 en pasos de 0.0625, o `null` (Pai: 0.5).
- **`shadow`:** `none` | `soft` | `default` | `strong` | `null`.
- **`logo.light` / `logo.dark`:** el **objeto completo** que devuelve `organization_theme_logo_confirm`, o `null`. Un string da «se esperaba objeto, recibido texto». La clave del logo claro debe contener `/theme/logo-light-`, y la del oscuro, `/theme/logo-dark-`.

## Dónde se ve cada token

| Token | Dónde se ve | Trampa |
|---|---|---|
| `sidebar` | **Marco exterior**: el menú lateral y lo que rodea al panel | — |
| `background` | **Panel interior** donde vive el contenido | Si la marca es «base de color con superficies blancas», el color va en `sidebar` y el blanco en `background`. En Ditto se puso al revés: crema dentro, blanco fuera |
| `accent-foreground` (al **80 %**) | **Texto de los items inactivos del menú** y placeholder de «Buscar…» | No es `sidebar-primary` ni `sidebar-foreground`. Si `accent-foreground` es el color de marca, todo el menú se pinta de ese color |
| `sidebar-foreground` (al 70 %) | Etiquetas de grupo («Pai», «Ajustes», «Proyecto») | El validador la mide también sobre el item activo |
| `sidebar-accent` | Hover del menú | — |
| Item activo del menú | En claro, `var(--background)`: una píldora del color del panel. En oscuro, **fijo `#232323`** (`--sidebar-item-active`) | No se tematiza en oscuro |
| Fondo de inputs (`--field`) | En claro, `var(--background)`. En oscuro, **fijo `#161616`** | No se tematiza. Choca con paletas oscuras tintadas (verde, oliva, navy); encaja con las neutras |
| `muted` | Track de las barras de progreso, cajas de estadísticas (a veces al 60 %), encabezado de tablas | En claro casi no se ve (ver «control» abajo) |
| `primary` / `primary-foreground` | Botón principal e icono del item activo | `primary` también debe servir como **texto** sobre `background` y `card` |
| `ring`, `brand-text` | Foco, enlaces, `code-token-link` | — |
| `radius` | Botones ≈ `radius`; items del menú ≈ `radius − 2px`; panel interior ≈ `2 × radius` | Medido: 0.1875rem da botón 3px, menú 1px y panel 7px; 0.25 da 4/2/8; 0.875 da unos 12/18 |
| `shadow: "none"` | `--shadow-strength: 0` | — |
| `font` | Reemplaza `--font-inter` | Solo las siete fuentes de la lista |

## Pares que exige el validador

En los dos modos. Texto ≥ 4.5:1; no texto ≥ 3:1.

| Texto ≥ 4.5 | Sobre |
|---|---|
| foreground | background |
| card-foreground, popover-foreground | card, popover |
| primary-foreground, secondary-foreground, accent-foreground, brand-foreground | su fondo |
| muted-foreground | background, card, muted, accent |
| **primary** | **background, card** |
| brand-text | background, muted |
| sidebar-foreground | sidebar y el item activo (`#232323` en oscuro) |
| sidebar-primary-foreground, sidebar-accent-foreground | su fondo |

| No texto ≥ 3 | Sobre |
|---|---|
| ring | background, card, muted |
| sidebar-ring, sidebar-primary | sidebar |
| primary | muted |
| **control** (interno de Pai: `#8f8f8f` en claro, `#6f6f6f` en oscuro) | **background, card, muted** |

**Consecuencia de «control»:** en claro, `muted` no puede ser más oscuro que ≈ L 0.975, y `background` que ≈ L 0.976 con croma ~0.02. Por eso el track de progreso y las cajas de stats quedan casi invisibles (1.04–1.07 contra blanco). Desde el tema no se arregla.

## Equivalencias de fuente que funcionaron

| Marca | Tema |
|---|---|
| Geist | `inter` |
| Nunito | `figtree` |
| Space Grotesk | `manrope` |
| Inter | `inter` |

Cuando no hay equivalente exacto, dilo.

## Superficies de referencia (contraste contra blanco)

- shadcn neutral: `muted`/blanco ≈ 1.10, `border`/blanco ≈ 1.25.
- Con fondos crema o tintados, sube `border` a ≈ 1.35–1.4.
