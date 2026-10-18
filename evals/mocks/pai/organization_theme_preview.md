---
type: agent
expect:
  organizationId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai MCP organization_theme_preview. Never persist data. Return JSON or an error. If theme is omitted, preview the published organization_theme_get theme with ok true.

Validate theme structure and retain the literal server error messages below.
- Reject missing/non-object theme or absent schemaVersion 1, light, dark or logo with `BAD_REQUEST: El tema no es válido; revisa los problemas indicados.` and a required-field issue for each missing key.
- shell must be null or sidebar, floating, header, dual-rail, section-tabs, framed, topbar, icon-rail.
- font must be null or inter, dm-sans, manrope, plus-jakarta-sans, figtree, source-serif-4, lora.
- radius must be null or between 0 and 1.25 inclusive in steps of 0.0625.
- Invalid shell/font/radius returns BAD_REQUEST with the offending key.
- Case-insensitive dark.accent #134e4a produces `{"path":"dark.accent","code":"contrast","message":"«muted-foreground» sobre «accent» en oscuro: 4.22:1; el mínimo es 4.5:1.","ratio":4.22,"required":4.5,"mode":"dark","pair":["muted-foreground","accent"]}`.
- A light pastel primary lighter than #22c55e produces a light.primary contrast issue with ratio 2.28, required 4.5 and pair primary/background. Other colors produce no issues.

On valid input return ok (true iff no issues), normalized theme (shell defaults to null), contrast issues, css `[data-theme-preview]{--primary:…}`, scope `[data-theme-preview]` and the available shells with ids null, sidebar, floating, header, dual-rail, section-tabs, framed, topbar, icon-rail.
