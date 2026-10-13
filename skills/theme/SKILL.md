---
name: theme
description: "Tema de marca de una organización cliente en Pai Console (organization_theme_*, solo staff en el MCP corp): extraer los tokens del producto real del cliente, convertirlos a OKLCH, mapearlos a los tokens del Portal, pasar el validador de contraste AA, subir los logos claro y oscuro (del tema y de la organización), publicar y verificar en el Portal en claro y oscuro. Úsalo cuando pidan theme, tema, marca, branding, colores de la organización, tokens de diseño, tipografía, radio o logo de la organización, o tematizar el Portal de un cliente."
argument-hint: "[organización] [sitio o app del cliente]"
compatibility: "Pai 0.2.5+ (MCP corp, solo staff)"
---

# Tema de marca de una organización

Lee antes el skill `pai-console`. El tema es lo que ven el Portal y las vistas del cliente: colores en claro y oscuro, fuente, radio, sombra y logos.

Las tools `organization_theme_*` son **solo para el staff de Pai en el MCP corp**, y corresponden a la pantalla de staff «Ajustes». Un cliente o el edge público no las listan. El logo de la organización (`organization_update`) pide además ser owner o admin de esa organización.

**Referencias:**
- `${CLAUDE_PLUGIN_ROOT}/skills/theme/references/token-map.md`: claves del tema, dónde pinta el Portal cada token y los pares que exige el validador.
- `${CLAUDE_PLUGIN_ROOT}/skills/theme/references/contrast-audit.js`: auditoría de contraste para correr en el Portal.

Todo lo de este skill se midió en el Portal de develop al tematizar Abraxa, Ditto y Latitude.sh. El preview del MCP valida pares abstractos; el Portal es la prueba.

## 1. Flujo

1. `organization_list` → `organization_theme_get`: tema publicado, borrador con sus `issues` e historial. Léelo antes de editar.
2. **Extrae los tokens de la fuente real** (§2).
3. Convierte a **OKLCH** (`"oklch(L C H)"`).
4. Mapea con la semántica de shadcn (§3) y el mapa del Portal (`token-map.md`).
5. `organization_theme_preview {theme}`: corrige cada `issue` (§4) hasta que no quede ninguno.
6. Sube los logos (§5) y ponlos en `theme.logo`.
7. `organization_theme_save_draft {theme}` → `organization_theme_publish`.
8. **Verifica en el Portal** en claro y oscuro (§6).
9. Si lo que decide es el gusto (por ejemplo, el color del acento), pregunta con opciones y una previsualización. No iteres a ciegas.

`theme` va **completo** en cada llamada: `{schemaVersion: 1, light, dark, font, radius, shadow, logo: {light, dark}}`. Una clave de color que no pongas queda con el valor de Pai.

## 2. De dónde sacar los tokens

En este orden:

1. **El dashboard o app del cliente**, si la persona tiene sesión. Es el sistema de producto y el que más se parece al Portal.
   - En Latitude.sh, el sitio de marketing era oliva y negro con Space Grotesk; el dashboard, gris neutro con Inter y radio 5px. El buen tema salió del dashboard.
   - Solo lectura. Si pide login, que la persona inicie sesión; **nunca escribas credenciales**.
2. El sitio público o el login.

**Cómo leer en el navegador:**
- **Variables CSS:** `getComputedStyle(document.documentElement)`, recorriendo las reglas de `document.styleSheets`.
- **Estilos computados de componentes reales:** botón primario, item activo del menú, input, card y borde. Muchos sitios traen las variables de shadcn por defecto sin usarlas; **confía en lo computado**.
- **Acento:** cuenta los colores por frecuencia.
- **Tipografía:** cuéntala por caracteres renderizados, no por reglas.

**Conversión:** un `lab()` de CSS es CIE Lab con blanco D50. Adáptalo a D65 (Bradford) antes de pasarlo a OKLab y OKLCH; si no, el matiz se corre.

## 3. Buenas prácticas (shadcn)

- Colores en OKLCH. Los neutros, **tintados** con el matiz de la marca a croma bajo (0.004–0.02), como las bases Mist y Olive de shadcn.
- Un solo acento, en `primary`.
- `secondary`, `muted` y `accent` son casi la misma superficie sutil (hover, selección, cabeceras).
- **Claro:** `background` blanco puro; el tinte vive en `sidebar`, bordes y grises.
  - `sidebar` es el **marco exterior** y `background` el **panel interior**. Si la marca es «base de color con superficies blancas», el color va en `sidebar`.
- **Oscuro:** `card`, `popover` y `sidebar` un escalón (+0.035 a +0.07 de L) sobre `background`.
  - Si la marca usa marco y página del mismo color (el dashboard de Latitude), iguálalos.
- **Menú:** el texto de los items inactivos es `accent-foreground` al 80 %. Si lo pones del color de marca, todo el menú se pinta de ese color.
- **Charts:** una rampa de 5 tonos del acento, o la paleta de datos real de la marca si existe.
- **Fuente:** solo `inter`, `dm-sans`, `manrope`, `plus-jakarta-sans`, `figtree`, `source-serif-4` o `lora`. Equivalencias en `token-map.md`; si no hay una exacta, dilo.
- **Radio:** el botón mide ≈ `radius`, el item del menú ≈ `radius − 2px` y el panel ≈ `2 × radius`. Para igualar un botón de 5px, usa `0.3125`.
- **No inventes.** Si el cliente tiene un modo oscuro genérico (Ditto: el neutral de shadcn por defecto), construye uno de marca con estas reglas y dilo.

## 4. Reglas del validador

Conócelas de antemano; la lista completa de pares está en `token-map.md`.

- **`primary` sobre `background` y `card` ≥ 4.5:1**, porque `primary` también es texto.
  - Un acento claro (lima, amarillo, crema) no puede ser `primary` en claro.
  - **Invierte el par:** `primary` oscuro con `primary-foreground` del color de marca (Latitude: negro oliva con texto lima).
  - En oscuro, el acento sí va como `primary`, con texto oscuro.
- **`ring` ≥ 3:1** sobre `background`, `card` y `muted`. **`sidebar-ring` y `sidebar-primary` ≥ 3:1** sobre `sidebar`. **`primary` ≥ 3:1** sobre `muted`.
- **`sidebar-foreground` ≥ 4.5:1 sobre el item activo**, que en oscuro es fijo `#232323`.
- **«control» ≥ 3:1 sobre `background`, `card` y `muted`.** «control» es un gris interno de Pai, no del tema: `#8f8f8f` en claro y `#6f6f6f` en oscuro.
  - En claro, `muted` no puede ser más oscuro que ≈ L 0.975, y `background` que ≈ L 0.976 con croma ~0.02.
  - Por eso el track de progreso y las cajas de stats quedan casi invisibles. **No se arregla desde el tema.**
- **Los problemas de AA se permiten en borrador, pero bloquean `publish`.** `save_draft` sí rechaza un esquema inválido o un logo de otra organización.

## 5. Logos

Hay **dos logos distintos** y hay que subir los dos:

| | Tema | Organización |
|---|---|---|
| Dónde se ve | Portal y vistas, en claro y oscuro | Avatar del selector de organizaciones y Ajustes › General |
| Formato | PNG, WebP o **SVG** ≤ 512 KB | **Solo PNG** ≤ 10 MB |
| Subida | `organization_theme_logo_upload_url {variant, contentType, size}` → PUT → `organization_theme_logo_confirm {storageKey: fileKey}` | `organization_logo_upload_url {size}` → PUT → `organization_update {logo: fileKey}` |
| Va en | `theme.logo.light` / `theme.logo.dark`: el **objeto completo** de `logo_confirm`, `{storageKey, contentType, bytes}` | `logo`: el `fileKey` (string) |

- Si pasas el `storageKey` como string en `theme.logo`, da «se esperaba objeto, recibido texto».
- El PUT lleva **exactamente** el `contentType` y el `size` declarados. La URL dura 5 min: sube de inmediato.
- **El logo claro es la versión oscura de la marca**, y viceversa (Abraxa: «A» negra en claro, blanca en oscuro). Sube cada uno con su `variant`: la clave del claro no sirve en `logo.dark`.
- **Buenas fuentes:** el `favicon.svg` del sitio, los logos del repo del cliente o el SVG inline del login. **Míralo antes de subirlo:** el `apple-touch-icon` de Ditto era un genérico ajeno a la marca.
- Para pasar de SVG a PNG, o subir sin pasar el archivo por la conversación, dibújalo en un `<canvas>` en el navegador y haz el PUT desde la página; el CORS del storage lo permite.

## 6. Verificar en el Portal

El preview no ve opacidades reales ni superficies casi idénticas. Después de publicar:

1. Abre el Portal de la organización y **recarga**.
2. Pega `contrast-audit.js` (javascript_tool de Chrome o la consola). Mide claro.
3. Llama `paiForceDark()`, espera 1–2 s y llama `paiContrastAudit()`. Mide oscuro sin cambiar la preferencia de la persona.
4. Lee:
   - el contraste mínimo y los fallos AA;
   - las superficies, comparadas con las de referencia de `token-map.md`: `border`/`background` ≈ 1.25, o ≈ 1.35–1.4 con fondos crema o tintados.
5. Mira también capturas: el menú, un formulario, una tabla y una página con barras de progreso.

## 7. Conducta

- El tema se puede revertir (`organization_theme_revert`). Aun así, **en producción confirma con la persona antes de `publish`**. En develop y staging puedes publicar para verificar.
- Al terminar, di siempre **qué no se pudo igualar** y a quién le toca:
  - la fuente, si no está disponible;
  - el item activo `#232323` y el campo `#161616` en oscuro, que son fijos;
  - el track de progreso y las cajas de stats sobre `muted`;
  - degradados, blur o glass, y botones ghost contra sólidos.
  Lo que es del Portal se lo toca al equipo de producto, no al tema.
- **No hagas:**
  - escribir credenciales en el sitio del cliente;
  - poner el `storageKey` como string en `theme.logo`;
  - usar un acento claro como `primary` en claro;
  - oscurecer `muted` en claro para que se vea el track: el validador lo rechaza;
  - publicar sin medir en el Portal.
