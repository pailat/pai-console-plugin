---
name: theme
description: "Tema de marca de una organización en Pai (Ajustes › Apariencia, solo staff, MCP corp): colores claro y oscuro, fuente, radio, sombra, logos y el app shell del Portal (shell), con contraste AA. Cubre leer el tema, proponer uno desde una marca, un logo o colores, previsualizarlo, guardar el borrador, publicar, volver a una versión anterior y subir logos. Úsalo cuando pidan tema, marca, branding, white-label, colores del Portal, logo del cliente, Apariencia, app shell, layout del Portal o «que el Portal se vea como su marca»."
argument-hint: "[organización] [marca, logo o colores]"
compatibility: "Pai 0.2.5+ (MCP corp, staff de Pai miembro de la organización)"
---

# Tema de la organización (Apariencia)

Lee antes el skill `pai-console`. El tema es la marca que el cliente ve en **su Portal** y en las vistas de Pai pintadas para su organización. Es lo mismo que edita Ajustes › Apariencia en el Portal: los mismos casos de uso y la misma auditoría.

Ejemplo completo y validado: `${CLAUDE_PLUGIN_ROOT}/skills/theme/examples/brand-theme.json`.

## Quién puede

- **Solo el staff de Pai** en el MCP corp (área `organization:appearance`, staff only). Las tools `organization_theme_*` no existen para un cliente ni para una persona solo de CRM.
- Además, debes **ser miembro** de la organización (`organizationId` de `organization_list`). Si no lo eres, `FORBIDDEN`: pide que te agreguen y no lo rodees.
- Ser «staff en organizaciones» (Administración › Usuarios › Roles) da Apariencia en el Portal, **no** en el MCP.

## Qué ve el cliente

| Estado | Lo ve el cliente | Dónde |
|---|---|---|
| Borrador (`save_draft`) | **No** | Solo en `organization_theme_get` y `organization_theme_preview` |
| Publicado (`publish`, `revert`) | **Sí, desde su siguiente carga** | Todo su Portal (colores, fuente, radio, sombra, logo y el shell), las vistas de `view_render` con su `organizationId` y las pantallas `PortalShell` de las pages canvas |

Las vistas con `PortalShell` toman el shell **del tema publicado**, no tienen prop para elegirlo. `organization_theme_preview` es el único lugar donde se ve un borrador.

## El tema

`theme` va **completo** en cada `preview` y `save_draft`. No es un patch: lo que no mandes se pierde del borrador.

```json
{ "schemaVersion": 1,
  "light": { "primary": "#0f766e", "primary-foreground": "#ffffff", "…": "…" },
  "dark":  { "primary": "#2dd4bf", "primary-foreground": "#042f2e", "…": "…" },
  "font": "plus-jakarta-sans", "radius": 0.75, "shadow": "soft", "shell": "floating",
  "logo": { "light": null, "dark": null } }
```

- **Colores** (`light` y `dark`): solo `#rrggbb` u `oklch(L C H)`, sin alfa, `var()` ni nombres. Las claves que no pongas quedan con las de Pai. Las editables son:
  - superficies: `background`, `foreground`, `card`, `card-foreground`, `popover`, `popover-foreground`;
  - acentos: `primary`, `primary-foreground`, `secondary`, `secondary-foreground`, `muted`, `muted-foreground`, `accent`, `accent-foreground`, `border`, `ring`;
  - azul de marca: `brand`, `brand-foreground`, `brand-text`;
  - gráficas: `chart-1` a `chart-5`;
  - barra lateral: `sidebar`, `sidebar-foreground`, `sidebar-primary`, `sidebar-primary-foreground`, `sidebar-accent`, `sidebar-accent-foreground`, `sidebar-border`, `sidebar-ring`.
- **Pai conserva** los colores semánticos (`destructive`, `success`, `warning`, `info`), los bordes de campos y controles y el resaltado de código: un error se lee como error en toda organización. No intentes cambiarlos.
- `font`: `inter` (la de Pai), `dm-sans`, `manrope`, `plus-jakarta-sans`, `figtree`, `source-serif-4`, `lora`, o `null`.
- `radius`: rem de 0 a 1.25, en pasos de 0.0625 (1 px), o `null` (Pai: 0.5).
- `shadow`: `none`, `soft`, `default`, `strong`, o `null`.
- `logo.light` / `logo.dark`: la referencia que devuelve `organization_theme_logo_confirm` (`{storageKey, contentType, bytes}`) tal cual, o `null`. `light` es para fondo claro y `dark` para fondo oscuro.

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

Elige por cómo trabaja el cliente, no por gusto. Con muchas secciones conviene `sidebar` o `header`. Con pocas y pantallas anchas, `topbar` o `icon-rail`. Si no hay razón para cambiarlo, deja `null`. El shell cambia la estructura, no el menú: las secciones son las del Portal.

## Contraste AA (lo que bloquea publicar)

El servidor mide cada par en claro **y** en oscuro:
- **Texto, 4.5:1:**
  - cada texto sobre su superficie (`foreground`/`background`, `card-foreground`/`card`, `primary-foreground`/`primary`, `secondary-foreground`/`secondary`, `accent-foreground`/`accent`, `brand-foreground`/`brand`…);
  - `muted-foreground` sobre `background`, `card`, `muted` **y `accent`**;
  - `primary` como texto sobre `background` y `card`;
  - `brand-text` sobre `background` y `muted`;
  - el texto de la barra lateral sobre `sidebar`, `sidebar-primary`, `sidebar-accent` y el ítem activo;
  - los textos semánticos de Pai sobre `background` y `card`.
- **No texto, 3:1:** `ring` sobre `background`, `card` y `muted`; `sidebar-ring` sobre `sidebar`; el control de Pai sobre `background`, `card` y `muted`; `primary` sobre `muted`; `sidebar-primary` sobre `sidebar`.
- No se miden los bordes ni las gráficas.

Cada problema llega como `{path, code: "contrast", message, ratio, required, mode, pair}`, por ejemplo «`muted-foreground` sobre `accent` en oscuro: 4.22:1; el mínimo es 4.5:1» con `path: "dark.accent"`. `path` señala **la clave que tú pusiste**: corrige esa, oscureciendo o aclarando el fondo o el texto, y vuelve a previsualizar.

Errores típicos:
- Un `accent` oscuro de marca rompe el texto secundario de Pai: `accent` también es fondo de `muted-foreground` (fila con hover).
- Si `primary` es un color claro (amarillo, verde lima), falla como texto sobre `background`. Usa un tono más oscuro de la marca para `primary` y deja el claro en `chart-*` o `brand`.
- El modo oscuro no es el claro invertido: dale a `dark` sus propios tonos (los de marca más claros, los fondos más oscuros).
- Poner solo `primary` y olvidar `primary-foreground`, o `sidebar` sin `sidebar-foreground`.

## Flujo

1. **Descubre:** `organization_list` → `organizationId` (debes ser miembro).
2. **Lee:** `organization_theme_get {organizationId}`. Da lo publicado, el borrador con sus `issues` y las últimas 10 versiones. Si hay borrador, **parte de él**; si no, de lo publicado; si no hay ninguno, de `schemaVersion: 1` con `light: {}`, `dark: {}` y todo lo demás en `null`.
3. **Propón** (desde una marca, un logo o colores): compón el tema completo. Si vas a iterar mucho, delega al agente `theme-designer`: hace el ciclo de preview sin llenar tu contexto y te devuelve el JSON.
4. **Previsualiza:** `organization_theme_preview {organizationId, theme}`. No guarda nada. Devuelve:
   - `ok` e `issues`;
   - el CSS que se aplicaría;
   - `shells`;
   - en hosts con MCP Apps, una vista con la muestra de componentes y el selector de shells.

   Itera hasta `ok: true`. Sin `theme`, previsualiza el borrador (o lo publicado, o el de Pai).
5. **Muéstralo y confirma** con la persona: los colores principales, la fuente, el shell y lo que cambia contra lo publicado.
6. **Guarda el borrador:** `organization_theme_save_draft {organizationId, theme}`. Lo publicado no cambia.
   - Se rechaza (`BAD_REQUEST`, `cause.code: "THEME_REJECTED"`, con `cause.issues`) por esquema, fuente, shell o logo.
   - El contraste **no** bloquea el borrador: vuelve en `issues`.
7. **Publica solo con un sí explícito** de la persona: `organization_theme_publish {organizationId}`. Publica el borrador, o `version` del historial. Se rechaza con la lista de problemas si no cumple AA, el esquema o sus logos. El cliente lo ve en su siguiente carga.
8. **Comprueba:** `organization_theme_get` (el publicado es tu versión). Para mostrarlo, `view_render` con `organizationId` (por ejemplo un `PortalShell` con su `area`, migas y usuario: tomará el shell y los colores publicados).

**Volver atrás:** `organization_theme_revert {organizationId, version, publish?}` copia la versión como borrador nuevo y, salvo `publish: false`, la publica. Se valida de nuevo: si ya no cumple AA o sus logos, se rechaza y nada cambia. Publicar y volver son destructivas (cambian lo que ve el cliente): confirma siempre, también en staging.

## Logos

1. Revisa el archivo: PNG, WebP o SVG de hasta **512 KB**. Necesitas `size` en bytes exactos (`stat -c %s` o `wc -c`).
2. `organization_theme_logo_upload_url {organizationId, variant: "light"|"dark", contentType, size}` devuelve una URL firmada que caduca en **5 min** y su `fileKey`.
3. `PUT` inmediato con exactamente ese `contentType` y esos bytes, por ejemplo `curl -X PUT -H "Content-Type: image/svg+xml" --data-binary @logo.svg "<url>"`.
4. `organization_theme_logo_confirm {organizationId, storageKey: <fileKey>}`: Pai lee el archivo, comprueba el tipo, sanea el SVG y devuelve la referencia.
5. Pon esa referencia **tal cual** en `theme.logo.light` o `theme.logo.dark` y sigue el flujo (preview → save_draft → publish).

- No subas el mismo archivo para las dos variantes si no se lee sobre fondo oscuro: pide la versión para fondo oscuro o deja `dark: null`.
- No es el logo de la organización (`organization_logo_upload_url`), que es otra cosa.

## Errores frecuentes

| Mensaje | Causa |
|---|---|
| `El tema no es válido; revisa los problemas indicados.` | Esquema, fuente, shell o logo; cada problema viene en `cause.issues` con su `path` |
| `Color no válido: usa #rrggbb u oklch(L C H).` | Un color con alfa, nombre, `rgb()` o `var()` |
| `Ese shell no existe.` / `Esa fuente no está permitida.` | Un `shell` o `font` fuera de las listas de arriba |
| `El radio va en pasos de 1px (0.0625rem).` | `radius` que no es múltiplo de 0.0625 |
| `El tema no se puede publicar: no cumple el contraste AA o tiene problemas.` | Publicar con `issues` de contraste: corrige, guarda otro borrador y publica |
| `No hay un borrador del tema que publicar.` | `publish` sin borrador ni `version` |
| `La clave del logo … es de la otra variante.` | Un logo `light` subido como `dark` o al revés |
| `La clave del logotipo no pertenece al tema de esta organización.` | Una referencia de logo de otra organización: súbelo aquí |
| `No se encontró el logotipo subido; vuelve a subirlo.` | `confirm` sin el `PUT`, o la URL caducó |
| `Esta versión del tema guardada ya no es válida; guarda un borrador nuevo.` | Una versión vieja que ya no pasa el esquema actual |

**Nunca** publiques sin confirmación, inventes una referencia de logo ni mandes un tema parcial creyendo que se fusiona.
