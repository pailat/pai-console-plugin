---
type: llm
focus: mock_calls
---

PASS solo si la llamada a `page_create` (la última, si hubo varias) cumple todo esto:
1. `path` en inglés, kebab-case y en carpeta (por ejemplo `prototypes/payment-simulator`), sin acentos ni espacios.
2. El contenido tiene un bloque `{type: "html"}` con `title` en español, `html` no vacío y `height` `"auto"` o un entero entre 120 y 4000. No hay `typeSlug`.
3. Chart.js se carga con `<script src>` desde `https://cdn.jsdelivr.net/npm/`, `https://cdnjs.cloudflare.com/` o `https://unpkg.com/` (o el script va inline). Ningún otro host de scripts.
4. Los datos y el cálculo van dentro del HTML: no hay `fetch`, XHR ni llamadas a APIs.
5. Los colores usan los tokens de Pai como variables CSS (al menos `var(--background)` y `var(--foreground)`, o `--card`, `--border`, `--primary`…) en vez de colores fijos para fondo y texto.
6. `audience` es `internal`, `summary` tiene 80 caracteres o menos e `idempotencyKey` está presente.
