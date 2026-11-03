---
name: iam
description: "Inspect and manage Pai IAM access through actual grants: principals, groups, roles, resource policies/bindings, deny rules, organization boundaries, access tests, audit, member visibility settings, own bindings, staff grants, and service accounts and tokens. Use for access diagnosis or explicitly requested permission changes."
metadata:
  compatibility: "Pai 0.2.5+ with granular IAM MCP tools"
---

# IAM and access

Read `../pai-console/SKILL.md`. Discover available tools and use `../../evals/mocks/pai/_tools.json` for exact nested schemas, enums and limits. IAM-only users may see iam_* tools without the rest of Console. A role name, staff label or visible button does not grant authority; resource authorization is evaluated on every invocation. A 404 can deliberately hide an inaccessible resource. Do not probe guessed IDs or create an alternative principal/group to bypass a denial.

## Diagnose before changing

- `iam_permission_catalog {organizationId?}` lists actual permissions; do not invent names or use retired crm:* permission strings as current grants.
- `iam_principal_list {query?,organizationId?}` / `iam_principal_get {userId,organizationId?}` identify people and existing access.
- `iam_access_test {resource,permissions,organizationId?}` tests the caller's access. `iam_access_explain {userId,permission,resource,organizationId?}` explains another person's access when allowed.
- Read `iam_policy_get {resource,organizationId?}`, `iam_deny_list {resource,organizationId?}`, and `iam_boundary_get {organizationId}` to understand explicit/inherited grants, conditions, denials and the organization boundary. Use returned canonical resource/principal shapes, not display labels.
- Omit organizationId only for an intentionally selected platform scope supported by the schema. Never fall back from a denied organization action to platform scope.

A folder/page grant can expose only Resources (`access: "resources"`) without `resourcemanager.projects.get`. It does not open other project sections or grant membership. Diagnose the concrete page, note, whiteboard, file or folder rather than assuming a denied overview means no resource access. Reader-relative paths conceal ancestors (`../resources/SKILL.md`). The organization Resources navigation separately tests `resources.folders.list` on the organization.

The retired `payments.milestoneCheckouts.create` permission and former alias `billing.milestonePayments.create` are absent from the current catalog and predefined roles. Use the fiscal Payments workflow (`../proposals-payments/SKILL.md`); do not grant or recreate the removed permission.

## Groups and roles

| Family | Read first | Authorized changes |
|---|---|---|
| Groups | iam_group_list; iam_group_get {groupId}; iam_group_member_list {groupId} | iam_group_create {key,name,description?}; iam_group_update {groupId,changes}; iam_group_delete {groupId}; iam_group_member_add {groupId,userIds}; iam_group_member_remove {groupId,userId} |
| Roles | iam_role_list; iam_role_get {roleId}; iam_permission_catalog | iam_role_create {key,name,permissions,description?,stage?}; iam_role_update {roleId,changes}; iam_role_delete {roleId} |

Predefined roles added in Pai 0.2.5 (read them with iam_role_get rather than relying on this summary; iam_role_list also shows the job roles, and `crm.workspaceOpener` is not grantable by hand because the CRM gives it when it opens a lead's workspace):

| Role | Scope | Permissions | Use |
|---|---|---|---|
| `connections.manager` | organization | Host registry lifecycle (list/get/create/approve/revoke and more) and `connections.hosts.manageTeam` | Effective Pai staff with an explicit binding. `manageTeam` widens each connection verb from the person's own hosts to the whole team's (`scope: "all"`); it does not grant the verb |
| `connections.runtime` | organization | Internal incarnation claim/activation/renewal/authorization/closure and gateway terminal redeem/report | Runtime authority only; no MCP/Portal/Console transport |
| `connections.terminal` | organization | `connections.terminals.attach`, `.list`, `.open`, `.terminate` | Pai staff with an explicit binding. Only the host's owner opens a terminal on it; MCP can list and terminate terminals, never open, attach or write (`../organizations/SKILL.md`) |
| `iam.serviceAccountAdmin` | organization | `iam.serviceAccounts.*` and `iam.serviceTokens.*` | Pai staff administering service accounts and their tokens; it grants no access to data and a token is not a session |
| `databases.viewer`, `.editor`, `.admin`, `.actionRunner`, `.protectedReader` | organization | Pai DB permissions (`databases.*`) | Customer-data roles: see the temporary-access rule below. `databases.protectedReader` adds protected properties such as amounts and needs a read permission as well |
| `resources.prdApprover` («Recursos · Aprobador de PRD») | resource | `resources.pages.get`, `resources.pages.confirmVersion` | A person who reads a PRD and confirms its current version, without editing, publishing or changing audience, status or owner. Bind it on that PRD page or its project; it cannot let an agent confirm (`../resources/SKILL.md`) |

`resources.pages.confirmVersion` is also part of resources.admin and the legacy organization/platform admin, owner and staff roles. The API Design permissions `knowledge.apiDesigns.create`, `.get`, `.list`, `.mock` and `.update` are in the catalog. Among predefined roles only `platform.admin` (all non-sensitive Pai permissions) carries them; an impersonated session is always denied API Design by a system rule. Others need an explicit grant before the `api-design` tools work (`../api-design/SKILL.md`). Do not create a role or binding for it unless the user explicitly asks.

**Customer data and temporary access.** Permissions the catalog marks as customer data (all `databases.*`) are, for anyone who is not a client of that organization, only grantable as a temporary, justified binding: a `condition.expiresAt` at most 72 hours ahead and a `justification` of 10 to 500 characters. Errors: `EXPIRY_REQUIRED`, `EXPIRY_TOO_LONG`, `JUSTIFICATION_REQUIRED` (all `invalid_input`) and `CUSTOMER_DATA_CLIENT_ONLY` (`forbidden`: only a client of the organization can give Pai staff access to its data). An impersonated session and a service account are always denied `databases.*` and `connections.*`. The organization owner role includes `databases.admin` and `databases.protectedReader`; Pai staff never hold a basic role from a membership.

These tools accept organizationId where exposed by their schema. Search/list before create. Preserve server restrictions on predefined roles, supported custom permissions, scope and launch stage. Explain the exact intended recipients, permissions, resource scope and effect before changing access; a user's request for diagnosis alone never authorizes granting access.

## Resource policy, deny and boundaries

- `iam_policy_set {resource,etag,bindings,organizationId?}` replaces the resource's complete explicit bindings and retains inherited ones. Read the current policy and retain unrelated explicit bindings. On ETAG_MISMATCH reread and reconcile; do not replay a stale full replacement.
- `iam_binding_add {resource,principal,roleId,justification?,condition?,etag?,organizationId?}` adds one grant after inspecting current policy. `principal.type` is `user`, `group` or `service`; a `service` principal uses the `serviceAccountId` and is accepted only from Pai staff, for an account of the same organization, on an organization, project or folder, with a role whose permissions all support custom roles (otherwise `ESCALATION`). `justification` (10 to 500 characters) is required with `condition.expiresAt` for customer-data roles (above); never invent one: ask the user for the real reason. `iam_binding_remove {bindingId,etag?,organizationId?}` removes the selected explicit grant; inherited access may remain. Send the etag from `iam_policy_get` to require that version, and on `ETAG_MISMATCH` reread and reconcile; without it the current version is used. `SELF_GRANT` means nobody changes their own access: ask another person.
- `iam_deny_create {resource,deniedPrincipals,deniedPermissions,exceptionPrincipals?,condition?,reason?,organizationId?}`; iam_deny_update {ruleId,changes}; iam_deny_delete {ruleId}. Inspect existing rules first and retain unrelated conditions/exceptions. Removing a denial can broaden effective access.
- `iam_boundary_set {organizationId,boundary}` changes an organization's permission ceiling. Read the existing boundary and use its schema (including the current etag when required inside boundary); do not guess a preset or permission list.
- `iam_settings_get {organizationId}` / `iam_settings_update {organizationId,membersSeeAllProjects}` controls organization members' project visibility. Review the affected population and current setting before applying it.

Keep authorization, native production prompts and CAS/etag checks. Test effective access after an authorized write, and explain inherited/deny/boundary effects without promising a role label alone changed access.

## Own access and staff grants (corp MCP)

- `iam_binding_list_mine {}` lists only the caller's own stored bindings with `id`, role, resource, organization, `expiresAt`, `justification`, `origin` (`manual`, `accessRequest`, `activation`, `breakGlass`), `grantedByName` and `renounceable`. It takes no organizationId and shows nobody else's access.
- `iam_binding_renounce {bindingId,organizationId?}` gives up one of the caller's own bindings with their real session (`iam.bindings.renounce`). Destructive: only after the user names the binding from the list and confirms; it cannot remove anyone else's access and cannot be used to "test" a denial.
- `iam_staff_grant_create {organizationId,userId,justification,expiresAt?}` gives **another** Pai staff person temporary staff entry to a client organization (an admin membership that takes no seat plus `orgs.legacyStaff`). `justification` is 10 to 500 characters and `expiresAt` is ISO 8601 with offset; 72 hours is both the default and the maximum. Never for yourself (`SELF_GRANT`; the CRM workspace flow covers that, `../crm/SKILL.md`); `STAFF_GRANT_MEMBER` (`conflict`) when the person is already a member. It is recorded in the audit and in the client's Pai access list, and the organization stops opening for that person at expiry. Confirm person, organization, reason and expiry before calling.
- `iam_staff_grant_end {organizationId,userId}` ends that person's membership and binding together; never your own. It returns `ended: false` when nothing was left, which is a success, not a reason to retry.

## Service accounts and tokens (corp MCP, Pai staff)

Machine access for an organization. Every call needs an effective human Pai staff session (not impersonated, not a service account) and the matching `iam.serviceAccounts.*` or `iam.serviceTokens.*` grant on that organization; a service-account token cannot manage IAM or identity. It is not a way around a denied grant: never create an account or token to bypass a refusal.

| Need | Tool |
|---|---|
| Find first | `iam_service_account_list {organizationId,limit?}` (1 to 200, default 100); `iam_service_account_get {serviceAccountId}`; `iam_service_token_list {serviceAccountId}` (metadata only: scope, permissions, rate limit, `expiresAt`, `revokedAt`, `lastUsedAt`) |
| Create | `iam_service_account_create {organizationId,name,description?,ownerUserId?}`: name 1 to 80 characters; `ownerUserId` defaults to the caller and must be a human |
| Change | `iam_service_account_update {serviceAccountId,changes}` (name, description, ownerUserId; partial) |
| Disable | `iam_service_account_disable {serviceAccountId}`; a disabled account cannot get new tokens (`SERVICE_ACCOUNT_DISABLED`). Revoke its tokens too when the goal is to cut access |
| Issue | `iam_service_token_create {serviceAccountId,name,scope,permissions,expiresAt,rateLimitPerMinute?}` |
| Rotate | `iam_service_token_rotate {serviceAccountId,tokenId,expiresAt,name?,scope?,permissions?,rateLimitPerMinute?,previousTokenGraceHours?}` |
| Revoke | `iam_service_token_revoke {serviceAccountId,tokenId}`; `tokenId: null` revokes every live token of the account. Idempotent: an already revoked token, or "all" with none live, answers the same without a new audit entry |

Token rules: `scope` is `{type: organization|project|folder, id}` inside the account's organization; `permissions` are 1 to 1000 catalog names, none the caller lacks on that scope (`ESCALATION`); `expiresAt` is ISO 8601 with offset, in the future and at most 90 days ahead (`SERVICE_TOKEN_EXPIRY_INVALID`); at most 5 live tokens per account (`SERVICE_TOKEN_LIMIT_REACHED`); `rateLimitPerMinute` is 1 to 600 (default 60). Request the narrowest scope and permission list and the shortest expiry that works. Rotation issues a replacement and keeps the old token valid for `previousTokenGraceHours` (0 to 168, default 24, never past its own expiry); a revoked or unknown token is `SERVICE_TOKEN_NOT_FOUND`. Errors for accounts: `SERVICE_ACCOUNT_NOT_FOUND`.

**Secrets are shown once.** `iam_service_token_create` and `iam_service_token_rotate` return the token value (`pai_st_…`) only in that response; no later call, list or get returns it. Never print, echo, log, summarize, store it in Knowledge, a page, a comment, a task or a chat, or put it in a description or name (the server rejects names that look like a token). Tell the user the response holds it and deliver it only through the channel the user names. If the response is lost, rotate or revoke and issue another; do not repeat a create hoping to see it again, because it uses another of the five slots. There is no idempotency key on these tools.

Issuing, rotating, revoking and disabling are destructive-class changes: state organization, account, scope, permissions and expiry, and wait for explicit approval each time.

## Audit and Pai access

- `iam_audit_list {organizationId?,actorId?,action?,before?,limit?}` inspects access changes.
- `iam_pai_access_list {organizationId,before?,limit?}` returns Pai people with access and their activity, roles, expirations and reasons. Follow nextBefore as an opaque cursor unchanged; do not replace it with a timestamp.

Preserve names and IDs from actual responses; do not request extra private data to diagnose access. `iam_audit_list` also records service account and token actions (`iam.service_account.*`, `iam.service_token.*`) and binding expiry or renunciation (`iam.binding.expired`, `iam.binding.renounced`). `examples/access-test.json` is a read-only schema example.
