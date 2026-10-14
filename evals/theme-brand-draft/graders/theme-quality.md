---
type: llm
focus: mock_calls
---

`organization_theme_get` devolvió el tema publicado v3 con `logo.light` = `{"storageKey":"df2f92f6-b25e-447d-986d-5d91e690c237/theme/logo-light-2b7c1d9e-3f4a-4c5b-8d6e-7f8a9b0c1d2e.svg","contentType":"image/svg+xml","bytes":4812}`. `organization_theme_preview` reporta un problema de contraste mientras `dark.accent` sea `#134e4a`.

PASS solo si la **última** llamada exitosa a `organization_theme_save_draft` cumple todo esto:
1. `theme` es completo: `schemaVersion: 1`, objetos `light` y `dark`, `font`, `radius`, `shadow`, `shell` y `logo` con `light` y `dark`.
2. `logo.light` es exactamente la referencia publicada (no `null`, no inventada) y `logo.dark` es `null`.
3. `light.primary` es `#0f766e` y `dark.primary` es `#2dd4bf`; `font` es `plus-jakarta-sans`; `shell` es `floating`; `radius` es mayor que 0.5, como máximo 1.25 y múltiplo de 0.0625.
4. `dark.accent` **no** es `#134e4a`: se ajustó por contraste a un tono más oscuro (o se omitió), y `light.accent` es `#f0fdfa`.
