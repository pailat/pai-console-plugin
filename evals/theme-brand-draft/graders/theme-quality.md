---
type: llm
focus: mock_calls
---

`organization_theme_get` returned published v3 with `logo.light` = `{"storageKey":"df2f92f6-b25e-447d-986d-5d91e690c237/theme/logo-light-2b7c1d9e-3f4a-4c5b-8d6e-7f8a9b0c1d2e.svg","contentType":"image/svg+xml","bytes":4812}`. `organization_theme_preview` reports a contrast issue while `dark.accent` is `#134e4a`.

PASS only if the last successful `organization_theme_save_draft` satisfies every condition:
1. `theme` is complete: `schemaVersion: 1`, `light`, `dark`, `font`, `radius`, `shadow`, `shell`, and `logo` with `light` and `dark`.
2. `logo.light` exactly preserves the published reference, and `logo.dark` is null.
3. `light.primary` is #0f766e; `dark.primary` is #2dd4bf; font is `plus-jakarta-sans`; shell is `floating`; radius is greater than 0.5, at most 1.25, and a multiple of 0.0625.
4. `dark.accent` is not #134e4a: it is darkened for contrast or omitted; `light.accent` remains #f0fdfa.
