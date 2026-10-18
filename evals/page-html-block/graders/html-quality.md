---
type: llm
focus: mock_calls
---

PASS only if the final `page_create` call satisfies every condition:
1. `path` uses English kebab-case within a folder, such as `prototypes/payment-simulator`, without accents or spaces.
2. Content includes a `{type: "html"}` block with a Spanish `title` as requested, nonempty `html`, and `height` equal to `"auto"` or an integer from 120 to 4000. No `typeSlug`.
3. Chart.js loads from `https://cdn.jsdelivr.net/npm/`, `https://cdnjs.cloudflare.com/`, or `https://unpkg.com/`, or is inline. No other script hosts.
4. Data and calculations are embedded: no fetch, XHR, or API calls.
5. Colors use Pai CSS tokens such as `var(--background)` and `var(--foreground)`, or `--card`, `--border`, and `--primary`, rather than fixed background/text colors.
6. `audience` is `internal`, `summary` is at most 80 characters, and `idempotencyKey` is present.
