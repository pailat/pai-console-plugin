# Pai Console integration checkpoint for 0.0.11

The reviewed source is `pai-portal` [`release/0.2.5` at `b194c6195`](https://github.com/pailat/pai-portal/commit/b194c6195), observed on 2026-10-29. It contains every merge since the 0.0.10 checkpoint (`df271445b`): #298, #300, #301, #302, #303, #304, #306, #307, #308, #309, #312, #314, #315, #316 and #317. A `git archive` of that commit under the session scratchpad, with dependencies installed there by `bun install --frozen-lockfile --ignore-scripts`, supplies the contracts and the in-memory MCP registration. No pai-portal checkout, database, user configuration or infrastructure was modified, and no MCP tool was called against any environment.

Only #316 and #317 change MCP behavior. The other merges are UI, performance, dependency, legacy cleanup or test changes; the generated literal tool list differs from 0.0.10 only by `asset_read`. The `knowledge_search` filters `c4Level` and `withCounts` are not in this release and are not documented.

## MCP asset images (#316)

- New read `asset_read {organizationId, projectId (nullable), assetId, size: "standard" | "thumbnail"}`, annotated read-only, idempotent and closed-world; permission `resources.assets.download`, the same use case and visibility rule as the Portal's `/api/pages/assets/<id>`. It returns a text line, one MCP `image` block and `structuredContent {asset, image}`; it has no `pai-view` view.
- Limits (`ASSET_READ_LIMITS`): standard ≤1568 px and 1.2 MP, thumbnail ≤512 px, output ≤1 MB as PNG, JPEG or WebP, input ≤40 MP, 10 s. A fitting original is sent unchanged; GIF gives its first frame; SVG is sanitized again and rasterized.
- Errors: indistinguishable `not_found`; `unprocessable` with `ASSET_NOT_IMAGE` (video and other types, which point to `asset_get`), `ASSET_IMAGE_TOO_LARGE`, `ASSET_IMAGE_UNREADABLE`, `ASSET_SVG_REFUSED`; `timeout` `ASSET_READ_TIMEOUT`; `unavailable` `STORAGE_UNAVAILABLE`.
- `page_read` (all views), `whiteboard_read` and `knowledge_get` add `assets: [{id, filename, kind, mimeType, width, height, sizeBytes, alt, readable}]`, only the assets the reader sees, always present. These are output changes; input schemas are unchanged.
- **Divergence from the planning document.** The mcp-images plan (§9) expected Knowledge not to record asset uses. The merged release adds `page_asset_use.node_id` (migration `20261029074143_knowledge-asset-uses`): a node body's assets appear in `usedIn` with `format: "knowledge"` and `shortId`, block `asset_delete` with `ASSET_IN_USE`, and a client sees an image used in a `visibility: "client"` node. The skills document the released behavior.

Guidance: `resources` gains «See images» (when to ask for an image, which size, never the href, GIF, SVG, video, errors, hosts without image display), `knowledge` gains «Images in nodes», `pai-console` adds the read line and error codes, and `agents/pai-explorer.md` allows `asset_read`. `skills/pai-console/references/tools.md` gains a generated section produced by `tools/gen-references.ts` from the contract constants.

## Old Portal links (#317)

Page writes (content, view `href`s), note creation and updates (only added links), Knowledge writes (properties and sources) and proposal saves refuse links to old Portal addresses (`/organization…`, `/portal…`, or absolute `/organization/projects/<uuid>…`) with `invalid_input` reason `LEGACY_LINK`. The `knowledge` skill no longer teaches `/organization/knowledge/<nodeId>`; `pai-console` adds the error row. View prose examples moved to `/acme/projects`; one reviewed translation (`tools/reference-translations-sync-b194c6195.json`) covers the changed `Link` description. The shared eval mocks now return slug-based URLs instead of `/portal/organization/projects/…`.

## Inventory

305 tools (123 reads, 182 writes) for the synthetic platform-admin inventory actor; upstream declares 307 names, with `proposal_accept` and `proposal_reject` still client-only.

## Evaluations

New case `asset-read-image` with mocks `asset_read`, `asset_get` and a `notas/incidente-checkout` note in `page_read`. Eval mocks cannot return MCP image content, so the case checks the workflow (note first, the listed image id at standard size, video through `asset_get`) and that the agent does not invent image text it never received. A real model reading pixels is upstream's evidence (`model-read.txt` in the mcp-images plan), not this suite's.
