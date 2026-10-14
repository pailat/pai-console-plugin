---
name: theme
description: "Tema de marca de una organización en Pai (Ajustes › Apariencia; organization_theme_*, solo staff en el MCP corp): colores claro y oscuro, fuente, radio, sombra, logos y el app shell del Portal (shell), con contraste AA. Cubre leer el tema, extraer los tokens del producto real del cliente (o de una marca, un logo o colores), convertirlos a OKLCH y mapearlos a los tokens del Portal, previsualizar, guardar el borrador, publicar, volver a una versión anterior, subir los logos del tema y de la organización, y verificar en el Portal en claro y oscuro. Úsalo cuando pidan tema, marca, branding, white-label, colores del Portal o de la organización, tokens de diseño, tipografía, radio, logo del cliente, Apariencia, app shell, layout del Portal o «que el Portal se vea como su marca»."
argument-hint: "[organización] [sitio, app, marca, logo o colores del cliente]"
compatibility: "Pai 0.2.5+ (MCP corp, staff de Pai miembro de la organización)"
---

# Tema de la organización (Apariencia)

Lee antes el skill `pai-console`. El tema es la marca que el cliente ve en **su Portal** y en las vistas de Pai pintadas para su organización. Es lo mismo que edita Ajustes › Apariencia en el Portal: los mismos casos de uso y la misma auditoría.

**Referencias:**
- `${CLAUDE_PLUGIN_ROOT}/skills/theme/examples/brand-theme.json`: ejemplo completo y validado (get → preview → save_draft).
- `${CLAUDE_PLUGIN_ROOT}/skills/theme/references/token-map.md`: claves del tema, dónde pinta el Portal cada token, los shells y los pares que exige el validador.
- `${CLAUDE_PLUGIN_ROOT}/skills/theme/references/contrast-audit.js`: auditoría de contraste para correr en el Portal.

Lo de §4, §5 y §8 se midió en el Portal de develop al tematizar Abraxa, Ditto y Latitude.sh. El preview del MCP valida pares abstractos; el Portal es la prueba.

## 1. Quién puede y qué ve el cliente

- **Solo el staff de Pai** en el MCP corp (área `organization:appearance`, staff only). Las tools `organization_theme_*` no existen para un cliente ni para una persona solo de CRM.
- Además, debes **ser miembro** de la organización (`organizationId` de `organization_list`). Si no lo eres, `FORBIDDEN`: pide que te agreguen y no lo rodees.
- El logo de la organización (`organization_update`, §7) pide además ser owner o admin de esa organización.

| Estado | Lo ve el cliente | Dónde |
|---|---|---|
| Borrador (`save_draft`) | **No** | Solo en `organization_theme_get` y `organization_theme_preview` |
| Publicado (`publish`, `revert`) | **Sí, desde su siguiente carga** | Todo su Portal (colores, fuente, radio, sombra, logo y shell), las vistas de `view_render` con su `organizationId` y las pantallas `PortalShell` de las pages canvas |

Las vistas con `PortalShell` toman el shell **del tema publicado** y no tienen prop para elegirlo. `organization_theme_preview` es el único lugar donde se ve un borrador.

## 2. Flujo

1. **Descubre:** `organization_list` → `organizationId`.
2. **Lee:** `organization_theme_get {organizationId}`. Da lo publicado, el borrador con sus `issues` y las últimas 10 versiones.
   - Si hay borrador, **parte de él**; si no, de lo publicado.
   - Si no hay ninguno, parte de `schemaVersion: 1` con `light: {}`, `dark: {}` y todo lo demás en `null`.
3. **Extrae los tokens de la fuente real** (§4) y conviértelos a **OKLCH** (`"oklch(L C H)"`).
4. **Compón el tema completo** con la semántica de shadcn (§5) y el mapa del Portal (`token-map.md`). Si vas a iterar mucho, delega al agente `theme-designer`: hace el ciclo de preview sin llenar tu contexto y te devuelve el JSON.
5. **Previsualiza:** `organization_theme_preview {organizationId, theme}`. No guarda nada. Devuelve:
   - `ok` e `issues`;
   - el CSS que se aplicaría;
   - `shells`;
   - en hosts con MCP Apps, una vista con la muestra de componentes y el selector de shells.

   Corrige cada `issue` (§6) hasta `ok: true`. Sin `theme`, previsualiza el borrador (o lo publicado, o el de Pai).
6. **Muéstralo y confirma** con la persona: los colores principales, la fuente, el shell y lo que cambia contra lo publicado. Si lo que decide es el gusto (por ejemplo, el color del acento), pregunta con opciones y una previsualización. No iteres a ciegas.
7. **Sube los logos** (§7) y ponlos en `theme.logo`.
8. **Guarda el borrador:** `organization_theme_save_draft {organizationId, theme}`. Lo publicado no cambia.
   - Se rechaza (`BAD_REQUEST`, `cause.code: "THEME_REJECTED"`, con `cause.issues`) por esquema, fuente, shell o un logo de otra organización.
   - El contraste **no** bloquea el borrador: vuelve en `issues`.
9. **Publica solo con un sí explícito** de la persona: `organization_theme_publish {organizationId}`. Publica el borrador, o `version` del historial. Se rechaza con la lista de problemas si no cumple AA, el esquema o sus logos.
10. **Comprueba:** `organization_theme_get` (el publicado es tu versión) y **verifica en el Portal** en claro y oscuro (§8). Para mostrarlo en la conversación, `view_render` con `organizationId` (por ejemplo un `PortalShell` con su `area`, migas y usuario: tomará el shell y los colores publicados).

**Volver atrás:** `organization_theme_revert {organizationId, version, publish?}` copia la versión como borrador nuevo y, salvo `publish: false`, la publica. Se valida de nuevo: si ya no cumple AA o sus logos, se rechaza y nada cambia.

## 3. El tema

`theme` va **completo** en cada `preview` y `save_draft`. No es un patch: lo que no mandes se pierde del borrador, y una clave de color que no pongas queda con el valor de Pai.

```json
{ "schemaVersion": 1,
  "light": { "primary": "#0f766e", "primary-foreground": "#ffffff", "…": "…" },
  "dark":  { "primary": "#2dd4bf", "primary-foreground": "#042f2e", "…": "…" },
  "font": "plus-jakarta-sans", "radius": 0.75, "shadow": "soft", "shell": "floating",
  "logo": { "light": null, "dark": null } }
```

- **Colores** (`light` y `dark`): solo `#rrggbb` u `oklch(L C H)`, sin alfa, `var()` ni nombres. Las editables son:
  - superficies: `background`, `foreground`, `card`, `card-foreground`, `popover`, `popover-foreground`;
  - acentos: `primary`, `primary-foreground`, `secondary`, `secondary-foreground`, `muted`, `muted-foreground`, `accent`, `accent-foreground`, `border`, `ring`;
  - azul de marca: `brand`, `brand-foreground`, `brand-text`;
  - gráficas: `chart-1` a `chart-5`;
  - barra lateral: `sidebar`, `sidebar-foreground`, `sidebar-primary`, `sidebar-primary-foreground`, `sidebar-accent`, `sidebar-accent-foreground`, `sidebar-border`, `sidebar-ring`.
- **Pai conserva** los colores semánticos (`destructive`, `success`, `warning`, `info`), los bordes de campos y controles y el resaltado de código: un error se lee como error en toda organización. No intentes cambiarlos.
- `font`: `inter` (la de Pai), `dm-sans`, `manrope`, `plus-jakarta-sans`, `figtree`, `source-serif-4`, `lora`, o `null`. Equivalencias en `token-map.md`; si no hay una exacta, dilo.
- `radius`: rem de 0 a 1.25, en pasos de 0.0625 (1 px), o `null` (Pai: 0.5). El botón mide ≈ `radius`, el item del menú ≈ `radius − 2px` y el panel ≈ `2 × radius`. Para igualar un botón de 5px, usa `0.3125`.
- `shadow`: `none`, `soft`, `default`, `strong`, o `null`.
- `logo.light` / `logo.dark`: la referencia que devuelve `organization_theme_logo_confirm` (`{storageKey, contentType, bytes}`) tal cual, o `null` (§7).

### El shell (app shell del Portal)

`shell` elige el marco del Portal. `null` es el de Pai: barra lateral insertada y la página en una tarjeta. `organization_theme_preview` devuelve la lista en `shells`; manda esa.

| `shell` | Es |
|---|---|
| `sidebar` | Barra lateral pegada al borde que se contrae a íconos; la página sobre el fondo |
| `floating` | Barra lateral flotante con borde y sombra, que se contrae a íconos |
| `header` | Encabezado de ancho completo (organización, búsqueda, usuario) y debajo la barra lateral |
| `dual-rail` | Riel de íconos con las áreas y un panel con el menú del área, que se oculta |
| `section-tabs` | Barra superior con las áreas como píldoras y debajo la barra lateral del área |
| `framed` | Áreas como pestañas arriba y un solo panel redondeado con el menú y la página |
| `topbar` | Sin barra lateral: áreas arriba y el menú del área como pestañas |
| `icon-rail` | Solo un riel angosto de íconos; la página ocupa el resto |

- Elige el que más se parezca a la app del cliente y a cómo trabaja, no por gusto. Con muchas secciones conviene `sidebar` o `header`; con pocas y pantallas anchas, `topbar` o `icon-rail`. Si no hay razón para cambiarlo, deja `null`.
- El shell cambia la estructura, no el menú: las secciones son las del Portal.
- El mapa de tokens se midió con el shell de Pai: si lo cambias, **vuelve a medir** marco, panel y menú en el Portal.

## 4. De dónde sacar los tokens

En este orden:

1. **El dashboard o app del cliente**, si la persona tiene sesión. Es el sistema de producto y el que más se parece al Portal.
   - En Latitude.sh, el sitio de marketing era oliva y negro con Space Grotesk; el dashboard, gris neutro con Inter y radio 5px. El buen tema salió del dashboard.
   - Solo lectura. Si pide login, que la persona inicie sesión; **nunca escribas credenciales**.
2. El sitio público o el login.
3. Una marca, un logo, una guía o colores que te pasen. No inventes colores de marca que no te dieron: si solo hay uno, deriva los demás de él y dilo.

**Cómo leer en el navegador:**
- **Variables CSS:** `getComputedStyle(document.documentElement)`, recorriendo las reglas de `document.styleSheets`.
- **Estilos computados de componentes reales:** botón primario, item activo del menú, input, card y borde. Muchos sitios traen las variables de shadcn por defecto sin usarlas; **confía en lo computado**.
- **Acento:** cuenta los colores por frecuencia.
- **Tipografía:** cuéntala por caracteres renderizados, no por reglas.

**Conversión:** un `lab()` de CSS es CIE Lab con blanco D50. Adáptalo a D65 (Bradford) antes de pasarlo a OKLab y OKLCH; si no, el matiz se corre.

## 5. Buenas prácticas (shadcn)

- Colores en OKLCH. Los neutros, **tintados** con el matiz de la marca a croma bajo (0.004–0.02), como las bases Mist y Olive de shadcn.
- Un solo acento, en `primary`. Cada `*-foreground` junto a su superficie.
- `secondary`, `muted` y `accent` son casi la misma superficie sutil (hover, selección, cabeceras).
- **Claro:** `background` blanco puro; el tinte vive en `sidebar`, bordes y grises.
  - `sidebar` es el **marco exterior** y `background` el **panel interior**. Si la marca es «base de color con superficies blancas», el color va en `sidebar`.
- **Oscuro:** no es el claro invertido. Dale tonos propios (la marca más clara, los fondos más oscuros).
  - `card`, `popover` y `sidebar` van un escalón (+0.035 a +0.07 de L) sobre `background`.
  - Si la marca usa marco y página del mismo color (el dashboard de Latitude), iguálalos.
- **Menú:** el texto de los items inactivos es `accent-foreground` al 80 %. Si lo pones del color de marca, todo el menú se pinta de ese color.
- **Charts:** una rampa de 5 tonos del acento, o la paleta de datos real de la marca si existe.
- **No inventes.** Si el cliente tiene un modo oscuro genérico (Ditto: el neutral de shadcn por defecto), construye uno de marca con estas reglas y dilo.

## 6. Contraste AA (lo que bloquea publicar)

El servidor mide cada par en claro **y** en oscuro (lista completa en `token-map.md`):
- **Texto, 4.5:1:**
  - cada texto sobre su superficie (`foreground`/`background`, `card-foreground`/`card`, `primary-foreground`/`primary`, `secondary-foreground`/`secondary`, `accent-foreground`/`accent`, `brand-foreground`/`brand`…);
  - `muted-foreground` sobre `background`, `card`, `muted` **y `accent`**;
  - `primary` como texto sobre `background` y `card`;
  - `brand-text` sobre `background` y `muted`;
  - el texto de la barra lateral sobre `sidebar`, `sidebar-primary`, `sidebar-accent` y el ítem activo, que en oscuro es fijo `#232323`;
  - los textos semánticos de Pai sobre `background` y `card`.
- **No texto, 3:1:** `ring` sobre `background`, `card` y `muted`; `sidebar-ring` y `sidebar-primary` sobre `sidebar`; `primary` sobre `muted`; el «control» sobre `background`, `card` y `muted`.
- No se miden los bordes ni las gráficas.

Cada problema llega como `{path, code: "contrast", message, ratio, required, mode, pair}`, por ejemplo «`muted-foreground` sobre `accent` en oscuro: 4.22:1; el mínimo es 4.5:1» con `path: "dark.accent"`. `path` señala **la clave que tú pusiste**: corrige esa, oscureciendo o aclarando el fondo o el texto, y vuelve a previsualizar.

Errores típicos:
- **Un acento claro** (lima, amarillo, crema) no puede ser `primary` en claro: falla como texto sobre `background`.
  - **Invierte el par:** `primary` oscuro con `primary-foreground` del color de marca (Latitude: negro oliva con texto lima), o un tono más oscuro de la marca, y deja el claro en `chart-*` o `brand`.
  - En oscuro, el acento sí va como `primary`, con texto oscuro.
- Un `accent` oscuro de marca rompe el texto secundario de Pai: `accent` también es fondo de `muted-foreground` (fila con hover).
- Poner solo `primary` y olvidar `primary-foreground`, o `sidebar` sin `sidebar-foreground`.
- **«control»** es un gris interno de Pai, no del tema: `#8f8f8f` en claro y `#6f6f6f` en oscuro.
  - En claro, `muted` no puede ser más oscuro que ≈ L 0.975, y `background` que ≈ L 0.976 con croma ~0.02.
  - Por eso el track de progreso y las cajas de stats quedan casi invisibles. **No se arregla desde el tema.**

## 7. Logos

Hay **dos logos distintos**; sube los dos:

| | Tema | Organización |
|---|---|---|
| Dónde se ve | Portal y vistas, en claro y oscuro | Avatar del selector de organizaciones y Ajustes › General |
| Formato | PNG, WebP o **SVG** ≤ 512 KB | **Solo PNG** ≤ 10 MB |
| Subida | `organization_theme_logo_upload_url {organizationId, variant, contentType, size}` → PUT → `organization_theme_logo_confirm {organizationId, storageKey: fileKey}` | `organization_logo_upload_url {organizationId, size}` → PUT → `organization_update {organizationId, logo: fileKey}` |
| Va en | `theme.logo.light` / `theme.logo.dark`: el **objeto completo** de `logo_confirm`, `{storageKey, contentType, bytes}` | `logo`: el `fileKey` (string) |

- `size` son los bytes exactos (`stat -f %z` en macOS, `wc -c`).
- La URL firmada caduca en **5 min**: haz el PUT de inmediato con exactamente ese `contentType` y esos bytes, por ejemplo `curl -X PUT -H "Content-Type: image/svg+xml" --data-binary @logo.svg "<url>"`.
- `logo_confirm` lee el archivo, comprueba el tipo, sanea el SVG y devuelve la referencia. Si pasas el `storageKey` como string en `theme.logo`, da «se esperaba objeto, recibido texto».
- **El logo claro es la versión oscura de la marca**, y viceversa (Abraxa: «A» negra en claro, blanca en oscuro). Sube cada uno con su `variant`: la clave del claro no sirve en `logo.dark`. Si no hay versión para fondo oscuro, pídela o deja `dark: null`.
- **Buenas fuentes:** el `favicon.svg` del sitio, los logos del repo del cliente o el SVG inline del login. **Míralo antes de subirlo:** el `apple-touch-icon` de Ditto era un genérico ajeno a la marca.
- Para pasar de SVG a PNG, o subir sin pasar el archivo por la conversación, dibújalo en un `<canvas>` en el navegador y haz el PUT desde la página; el CORS del storage lo permite.

## 8. Verificar en el Portal

El preview no ve opacidades reales ni superficies casi idénticas. Después de publicar:

1. Abre el Portal de la organización y **recarga**.
2. Pega `contrast-audit.js` (javascript_tool de Chrome o la consola). Mide claro.
3. Llama `paiForceDark()`, espera 1–2 s y llama `paiContrastAudit()`. Mide oscuro sin cambiar la preferencia de la persona.
4. Lee:
   - el contraste mínimo y los fallos AA;
   - las superficies, comparadas con las de referencia de `token-map.md`: `border`/`background` ≈ 1.25, o ≈ 1.35–1.4 con fondos crema o tintados.
5. Mira también capturas: el menú, un formulario, una tabla y una página con barras de progreso.

## 9. Errores frecuentes

| Mensaje | Causa |
|---|---|
| `El tema no es válido; revisa los problemas indicados.` | Esquema, fuente, shell o logo; cada problema viene en `cause.issues` con su `path` |
| `Color no válido: usa #rrggbb u oklch(L C H).` | Un color con alfa, nombre, `rgb()` o `var()` |
| `Ese shell no existe.` / `Esa fuente no está permitida.` | Un `shell` o `font` fuera de las listas de §3 |
| `El radio va en pasos de 1px (0.0625rem).` | `radius` que no es múltiplo de 0.0625 |
| `El tema no se puede publicar: no cumple el contraste AA o tiene problemas.` | Publicar con `issues` de contraste: corrige, guarda otro borrador y publica |
| `No hay un borrador del tema que publicar.` | `publish` sin borrador ni `version` |
| `La clave del logo … es de la otra variante.` | Un logo `light` subido como `dark` o al revés |
| `La clave del logotipo no pertenece al tema de esta organización.` | Una referencia de logo de otra organización: súbelo aquí |
| `No se encontró el logotipo subido; vuelve a subirlo.` | `confirm` sin el `PUT`, o la URL caducó |
| `Esta versión del tema guardada ya no es válida; guarda un borrador nuevo.` | Una versión vieja que ya no pasa el esquema actual |

## 10. Conducta

- Publicar y volver atrás cambian lo que ve el cliente: **confirma siempre** antes de `publish` o `revert`, también en develop y staging.
- Al terminar, di siempre **qué no se pudo igualar** y a quién le toca:
  - la fuente, si no está disponible;
  - el item activo `#232323` y el campo `#161616` en oscuro, que son fijos;
  - el track de progreso y las cajas de stats sobre `muted`;
  - degradados, blur o glass, y botones ghost contra sólidos.

  Lo que es del Portal le toca al equipo de producto, no al tema.
- **Nunca:**
  - escribas credenciales en el sitio del cliente;
  - publiques sin confirmación ni sin medir en el Portal;
  - inventes una referencia de logo o pongas el `storageKey` como string en `theme.logo`;
  - mandes un tema parcial creyendo que se fusiona;
  - uses un acento claro como `primary` en claro;
  - oscurezcas `muted` en claro para que se vea el track: el validador lo rechaza.
