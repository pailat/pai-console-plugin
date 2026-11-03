---
name: spaces
description: "Publish and operate database Spaces in Pai Console: register a Space, freeze draft versions, publish and deploy them with CAS, then query, create and update records, read record events and run published record actions (space_*, record_* tools). Also covers the Knowledge action section databaseAction. Use for Spaces, Pai DB records, publishing or deploying a Space version, comparing versions, record queries with filters and pagination, or running a record action."
argument-hint: "[organization] [space slug | space version | record id]"
compatibility: "Pai 0.2.5+ (MCP corp, database Spaces)"
---

# Database Spaces and their records

Read shared `pai-console` first through the current client's skill mechanism (environment, discovery, CAS, idempotency, errors). Spaces are corp MCP only, scoped to one organization: every call takes `organizationId`. There is no Portal screen for these tools. Product and ERD design live in Knowledge (`../erd/SKILL.md`, `../screens/SKILL.md`, `../products/SKILL.md`); this skill publishes that design and operates the resulting data.

Full tool inventory: `../pai-console/references/tools.md`.

## Authorization

- Every tool first requires Space admission, which is the `databases.databases.list` permission on the organization. Publication tools additionally need `databases.databases.create` / `databases.databases.update`.
- Records use the Pai DB primitive grants: `databases.records.list` (`record_query`), `databases.records.get` (`record_get`, `record_events`), `databases.records.create`, `databases.records.update`, `databases.actions.run` (and `databases.records.get`) for `record_action_run`. A missing grant is `FORBIDDEN`; never infer one from a role name and never attempt a different route. Diagnose with `../iam/SKILL.md`.
- The `permissionNamespace` of a Space (`space.<name>`) is metadata only in this release. It is not an evaluated control: do not describe it as granting or restricting anything.
- Sessions that run on behalf of a Pai Agent chat do not receive these generic tools; use a direct connection.

## Lifecycle: register, draft, publish, deploy

1. **Discover:** `space_list {organizationId, space?}` lists deployed Spaces (a slug filters). A Space that is registered but not deployed does not appear: that is not proof it does not exist, so before `space_create` also ask the person for the slug and check Knowledge/product state.
2. **Register** (once): `space_create {organizationId, slug, label, permissionNamespace, icon?, audience?, appProductId?}`. `slug` is kebab-case (`^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`, max 100). `permissionNamespace` matches `^space\.[a-z][a-zA-Z0-9]*$`. `audience` is `console`, `portal` or `both` (default `both`); `icon` defaults to `layout-grid`; `appProductId` is nullable and a draft may precede the App. Retrying the same `(organizationId, slug)` with the same input returns the existing Space; a different input is a conflict (`SPACE_EXISTS`). Built-in slugs are reserved (`SPACE_BUILTIN_SLUG`).
3. **Edit metadata:** `space_update {organizationId, id, expectedRevision, ...fields}` with CAS. Read the Space first (`space_list`), pass its `revision`, and re-read after a conflict (`SPACE_REVISION_CONFLICT`); never retry blind.
4. **Freeze the design:** product versions come first. `product_version_create` freezes the Knowledge manifest into a product draft and `product_version_publish` publishes it with `expectedRevision` (see `../products/SKILL.md`). The Space version only points at published product versions (`SPACE_PRODUCT_VERSION_NOT_PUBLISHED` otherwise).
5. **Draft a Space version:** `space_version_create {organizationId, spaceId, semver, productVersions:[{productId, productVersionId}], config?}`. `semver` is a SemVer 2.0 string. `productVersions` has 1 to 100 entries with no duplicate product. Retrying the same `(space, semver)` with identical input is idempotent; a different input for an existing semver is `SPACE_VERSION_EXISTS`. If the frozen design has several `api` nodes, `config.apiNodeIds` must select which pinned ones to publish; one node needs no selection; none publishes without an API contract.
6. **Review:** `space_version_get {spaceId, spaceVersionId}` (status `draft`, `published`, `archived`; composition and deployments, no manifest content), `space_versions {spaceId, limit?, offset?}` (`limit` 1-100, default 50; advance `offset` until fewer than `limit` items return) and `space_version_compare {spaceId, beforeId, afterId}` (compiled contract diff: models, API, config and product semvers). Compare before publishing over a deployed version and report breaking differences to the person.
7. **Publish:** `space_version_publish {organizationId, spaceId, spaceVersionId, environment, expectedRevision}`. This one call provisions the models and compiles the APIs, marks the version published and deploys it to `environment` (`development`, `staging` or `production`; `preview` is not supported). `expectedRevision` is the deployment's revision for that environment, and `0` when none exists yet. Read it from `space_version_get`/`space_versions` first. It is a production-affecting write: state the version, environment and compare result and wait for explicit confirmation before calling it, especially for `production`. Published versions keep their documents and sha unchanged.
8. **Redeploy or roll back:** `space_deploy` takes the same inputs for an already published version, for example moving an environment to a prior published version. Same CAS and confirmation rules.
9. **Archive:** `space_version_archive {spaceId, spaceVersionId}` is destructive. Only a published version that is not deployed in any environment can be archived (`SPACE_VERSION_DEPLOYED` otherwise). Confirm with the person first.

Publishing migrates the shared data of the source. If the deployed schema is no longer the current one, reads and writes answer `SPACE_DEPLOYMENT_STALE` until the deployment is moved. Data is not isolated per environment in this release: say so when the person expects a staging copy.

A contract that cannot be satisfied fails with `SPACE_CONTRACT_UNSATISFIABLE` and `issues: [{operationId, pointer, reason}]`; the whole publish is rolled back (including provisioned databases, sources and schemas). Report each issue verbatim and fix the Knowledge design (ERD, API design, action nodes) rather than retrying. Query requests in the API are replaced by the canonical Pai DB query schema and the publish returns warnings with a `pointer`; relay them.

## Reading data

- `space_schema {organizationId, space}` returns the published schema in this instance's environment: the source IDs, properties and actions. Always call it before the first record call in a Space; never guess `sourceId`, property keys, select option IDs or action keys.
- Record tools take `space` (the slug), plus `sourceId` and `operationId`. `sourceId` selects the entity. When several operations of the same kind are published, name `operationId` (it comes from the published API contract); an ambiguous or unmatched selection fails as `SPACE_OPERATION_NOT_FOUND`.
- Projected tools: a deployed Space may also expose dynamic tools named `<space_slug_in_snake>_...`. Each requires `spaceVersionId` (announced as a constant in its schema). If the Space moves versions between listing and calling, the call fails `SPACE_TOOL_STALE`: list the tools again and repeat with the new version; never reuse an old UUID.

### `record_query`

`record_query {organizationId, space, sourceId?, operationId?, input}` with `input`:

- `filter`: predicate `{kind:"predicate", property, type, op, value}` or `{kind:"and"|"or", filters:[...]}`. At most 8 levels, 100 nodes, 25 children per group. Operators by type: `title`/`text`/`url` `eq ne contains startsWith endsWith`; `number`, `date`, `money` `eq ne gt gte lt lte`; `select`/`status` `eq ne in notIn` (values are option IDs); `checkbox` `eq ne`; `people`/`relation`/`files` `contains notContains` (a record or file ID); any type `isEmpty isNotEmpty`. The predicate `type` must equal the property's type, `money` currency must match, and dates must match `includeTime`.
- `sort`: up to 5 terms `{field:"property", property, direction:"asc"|"desc", nulls:"first"|"last"}` or `field` of `id`, `createdAt`, `updatedAt`. `people`, `relation` and `files` properties are not sortable. `id` can only be last and is appended as the stable tie-breaker.
- `limit`: 1-200, default 50. `includeArchived`: default false.
- `cursor`: take `nextCursor` from the previous response, pass it back unchanged with the same filter and sort, and continue while `hasMore` is true. A cursor is bound to the query; changing the filter or sort needs a new query without a cursor. Never craft or edit a cursor (`DATABASE_INVALID_CURSOR`).
- Aggregations use an operation published as an aggregation query: `aggregations` of `{op:"count", as}` or `{op:"sum", property, as}` (number or money only), `groupBy` up to 3 (by property or by `date` period with `timeZone`), `limit` up to 1000. Money sums are buckets per currency; never add amounts of different currencies. If `truncated` is true the groups are partial.

Queries are limited to 120 requests per minute per organization; a refusal is `SPACE_RATE_LIMITED`. Back off instead of looping.

Respond with the displayed amounts as MXN or the stored currency, and dates in `America/Mexico_City`, per `../pai-console/SKILL.md`.

### `record_get` and `record_events`

`record_get {organizationId, space, sourceId?, operationId?, recordId}` returns the record with its `revision`. `record_events` takes `input: {cursor?, limit?}` (`limit` 1-200); no other key is allowed. Its `nextCursor` is signed and bound to the person, organization, version and record; pass it back unchanged while `hasMore` is true.

## Writing records

Every write requires `idempotencyKey` (1-128 characters) and `expectedRevision` (integer, at least 1), and the input is checked against the published contract: an unknown or undeclared property is rejected, and protected properties follow their projection.

- **Idempotency key:** generate one fresh unique key per intended write (for example a UUID) and reuse it only to retry the same call after a timeout or transport error. The same key with the same payload replays the stored result; the same key with a different payload is `DATABASE_IDEMPOTENCY_CONFLICT`. A missing key is `DATABASE_IDEMPOTENCY_REQUIRED`. Never reuse a key for a different record or change.
- **Create:** `record_create {organizationId, space, sourceId?, operationId?, idempotencyKey, expectedRevision, input}` where `input` holds property values by key, plus the optional reserved `body`. The tool schema requires `expectedRevision`, but creating has no prior revision, and the runtime does not apply it to creates; pass `1` and rely on the idempotency key. Search before create: run `record_query` with a filter on the natural key (for example a unique code or title) to avoid duplicates, and report what you found.
- **Update:** `record_update {..., recordId, idempotencyKey, expectedRevision, input}` with only the changed properties and optional `body`. Read the record with `record_get` immediately before, pass its `revision` as `expectedRevision`, and on `DATABASE_REVISION_CONFLICT` (the tool error class is `PRECONDITION_FAILED`) re-read, reconcile with the person's intent and retry with a new idempotency key only if the change still makes sense. Never overwrite a newer revision blindly. A successful update returns the new `revision`.
- **Archived records** reject actions and updates with `DATABASE_REVISION_CONFLICT`.
- Money values carry their currency, selects and statuses use option IDs from `space_schema`, relations use record IDs the person may read. Do not invent them.

### `record_action_run`

`record_action_run {organizationId, space, sourceId?, operationId?, recordId, key, idempotencyKey, expectedRevision, input}` runs a published action `key` on one record. Actions are a closed, typed definition compiled at publish time, with no code, SQL, callbacks or webhooks. Run order, in one transaction with all-or-nothing effect:

1. the `input` is validated against the action's typed `input` (unknown keys are rejected) and its relation targets are authorized;
2. `expectedRevision` must equal the record's current revision;
3. every `checks` entry (`left op right` with `eq ne gt gte lt lte`) must hold, otherwise `DATABASE_RULE_VIOLATION`;
4. the `stateMachine` requires the record's `property` to be in `from`, otherwise `DATABASE_RULE_VIOLATION`; on success the property becomes `to`;
5. effects apply: `update`, `create` (a new record in another entity, which needs `databases.records.create`), `relate`, `set_status`, and `reconcile` (validates that the allocations sum correctly to `amount`, with the money errors below).

The result is `{record, created}`: the updated record and any records the action created. Side effects are real, so treat it as a write needing confirmation: describe the action's checks, state transition and the records it will create or change (from `space_schema`), and call it only after explicit human intent for that record. Never run actions in a loop over a query result unless the person confirmed the exact set. Retry only with the same `idempotencyKey` and payload; a new key runs the action again. An unknown `key` fails as `DATABASE_RULE_VIOLATION`.

## Knowledge `action.databaseAction`

The `action` node (`../screens/SKILL.md`) accepts an optional `databaseAction` section: a typed, closed definition of a Pai DB action. It is the authority for execution; the narrative `inputs` table is documentation only. It is validated at write time and resolved against the pinned entities when the Space version is published. Schemas resolved at publish become part of the immutable schema version; to change an action, edit the node and publish a new Space version.

Shape: `{entity, key, input, stateMachine?, checks, effects}`.

- `entity`: the Knowledge entity reference (a design reference, never a runtime `sourceId`) the action runs on; `key`: the action key `record_action_run` uses.
- `input`: typed property designs, with no `id`, `organizationId`, `sourceId` or `revision`; a relation input names its `target` entity by reference, not by runtime ID.
- Operands are `{from:"input", key}`, `{from:"record", key}`, `{from:"literal", value}` or `{from:"recordId"}` (resolves to the current record's ID; use it for relation values).
- `checks`: up to 100 `{left, op, right}`; `stateMachine`: `{property, from:[...], to}`.
- `effects` (1-100): `update {properties}`, `create {entity, properties}`, `relate {property, value}`, `set_status {property, value}`, `reconcile {amount, allocations}`.
- Referenced entities must be part of the frozen product versions; otherwise publishing fails (for example `SPACE_RELATION_TARGET_NOT_PINNED`, `SPACE_DATA_MODEL_NOT_PINNED`). Existing action nodes without `databaseAction` remain valid and unchanged.

Design and confirmation rules follow `../knowledge/SKILL.md` (search before create, CAS with `expectedRevision`). Do not confirm decisions or human versions from an agent.

## Literal errors

Messages are Spanish server text; quote them, keep these codes verbatim.

| Code | When | What to do |
|---|---|---|
| `DATABASE_REVISION_REQUIRED` | update or action without a usable revision | re-read and pass `expectedRevision` |
| `DATABASE_REVISION_CONFLICT` | stale revision or archived record | re-read, reconcile, retry deliberately |
| `DATABASE_IDEMPOTENCY_REQUIRED` / `DATABASE_IDEMPOTENCY_CONFLICT` | no key, or key reused with a different payload | new key for a new write; same key only for the same retry |
| `DATABASE_INVALID_PROPERTY` / `DATABASE_INVALID_VALUE` | unknown key or wrong value type | correct from `space_schema` |
| `DATABASE_INVALID_FILTER` / `DATABASE_QUERY_LIMIT` / `DATABASE_INVALID_CURSOR` | bad filter (pointer in `cause`), limit above bounds, edited cursor | fix the query; drop the cursor |
| `DATABASE_REFERENCE_INVALID` | relation target missing or not readable | search the target again |
| `DATABASE_RULE_VIOLATION` | check, state machine, unknown action key | explain the rule; do not bypass |
| `DATABASE_CURRENCY_MISMATCH` / `DATABASE_MONEY_OVERFLOW` | currency or amount problem | correct the amounts |
| `DATABASE_SCHEMA_INCOMPATIBLE` | input does not match the schema version | re-read `space_schema` |
| `SPACE_NOT_FOUND`, `SPACE_OPERATION_NOT_FOUND` | no Space, deployment or operation | check the slug, deployment and `operationId` |
| `SPACE_DEPLOYMENT_STALE` | deployed schema is not current | move the deployment (`space_deploy`) |
| `SPACE_TOOL_STALE` | projected tool moved version | list tools again |
| `SPACE_RATE_LIMITED` | over 120 requests per minute | wait, do not loop |
| `SPACE_CONTRACT_UNSATISFIABLE` | publish failed; see `issues` | fix the design |
| `SPACE_VERSION_EXISTS`, `SPACE_EXISTS`, `SPACE_REVISION_CONFLICT` | same key with different input; stale Space revision | read the existing one; re-read the revision |
| `SPACE_DEPLOYMENT_REVISION_CONFLICT` | stale deployment `expectedRevision` on publish or deploy | re-read the deployment revision and ask again |
| `SPACE_DESIGN_REVISION_CONFLICT` | two frozen manifests pin different revisions of one node or edge | align the product versions, then freeze again |
| `SPACE_VERSION_DEPLOYED` | archiving a deployed version | deploy another version first |
| `SPACE_PRODUCT_VERSION_NOT_PUBLISHED` | draft composition | publish the product version first |

The tool error classes are `PRECONDITION_FAILED` for revision problems, `CONFLICT` for idempotency conflicts and `BAD_REQUEST` for the other database errors. Unverified: the exact wording of Space publication errors beyond the codes above; report the server message as received.
