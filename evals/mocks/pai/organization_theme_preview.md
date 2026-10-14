---
type: agent
expect:
  organizationId: string
abort_when: "Nunca abortes; responde siempre como el servidor."
---

Actúas como la tool `organization_theme_preview` del MCP de Pai. No guarda nada. Responde solo con JSON.

- Si `theme` falta, no es un objeto o le falta `schemaVersion: 1`, `light`, `dark` o `logo`: error `BAD_REQUEST: El tema no es válido; revisa los problemas indicados.` con una línea `- <clave>: Obligatorio.` por cada una que falte.
- Si `shell` no es null ni uno de sidebar, floating, header, dual-rail, section-tabs, framed, topbar, icon-rail: error `BAD_REQUEST: El tema no es válido; revisa los problemas indicados.\n- shell: Ese shell no existe.`
- Si `font` no es null ni uno de inter, dm-sans, manrope, plus-jakarta-sans, figtree, source-serif-4, lora: error igual con `- font: Esa fuente no está permitida.`
- Si `radius` no es null y (es mayor que 1.25, negativo o no es múltiplo de 0.0625): error igual con `- radius: El radio va en pasos de 1px (0.0625rem).` (o el máximo).
- Contraste: si `dark.accent` vale `#134e4a` (sin importar mayúsculas), hay un issue `{"path":"dark.accent","code":"contrast","message":"«muted-foreground» sobre «accent» en oscuro: 4.22:1; el mínimo es 4.5:1.","ratio":4.22,"required":4.5,"mode":"dark","pair":["muted-foreground","accent"]}`. Si `light.primary` es más claro que `#22c55e` (un verde, amarillo o color pastel claro), hay un issue `{"path":"light.primary","code":"contrast","message":"«primary» sobre «background» en claro: 2.28:1; el mínimo es 4.5:1.","ratio":2.28,"required":4.5,"mode":"light","pair":["primary","background"]}`. Ningún otro color da issues.

Sin errores, responde `{"ok":<true si no hay issues>,"theme":<el theme recibido, con shell null si faltaba>,"issues":[<issues de contraste>],"css":"[data-theme-preview]{--primary:…}","scope":"[data-theme-preview]","shells":[{"id":null,"label":"Pai","description":"Barra lateral insertada, página en una tarjeta.","source":"app-shell-3"},{"id":"sidebar","label":"Barra lateral"},{"id":"floating","label":"Flotante"},{"id":"header","label":"Encabezado completo"},{"id":"dual-rail","label":"Riel y panel"},{"id":"section-tabs","label":"Áreas arriba"},{"id":"framed","label":"Marco único"},{"id":"topbar","label":"Solo barra superior"},{"id":"icon-rail","label":"Riel de íconos"}]}`. Sin `theme` en la entrada, previsualiza el tema publicado de `organization_theme_get` (ok true).
