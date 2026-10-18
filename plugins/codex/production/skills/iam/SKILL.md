---
name: iam
description: "Inspect and manage Pai IAM access through actual grants: principals, groups, roles, resource policies/bindings, deny rules, organization boundaries, access tests, audit and member visibility settings. Use for access diagnosis or explicitly requested permission changes."
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

## Groups and roles

| Family | Read first | Authorized changes |
|---|---|---|
| Groups | iam_group_list; iam_group_get {groupId}; iam_group_member_list {groupId} | iam_group_create {key,name,description?}; iam_group_update {groupId,changes}; iam_group_delete {groupId}; iam_group_member_add {groupId,userIds}; iam_group_member_remove {groupId,userId} |
| Roles | iam_role_list; iam_role_get {roleId}; iam_permission_catalog | iam_role_create {key,name,permissions,description?,stage?}; iam_role_update {roleId,changes}; iam_role_delete {roleId} |

These tools accept organizationId where exposed by their schema. Search/list before create. Preserve server restrictions on predefined roles, supported custom permissions, scope and launch stage. Explain the exact intended recipients, permissions, resource scope and effect before changing access; a user's request for diagnosis alone never authorizes granting access.

## Resource policy, deny and boundaries

- `iam_policy_set {resource,etag,bindings,organizationId?}` replaces the resource's complete explicit bindings and retains inherited ones. Read the current policy and retain unrelated explicit bindings. On ETAG_MISMATCH reread and reconcile; do not replay a stale full replacement.
- `iam_binding_add {resource,principal,roleId,condition?,etag?,organizationId?}` adds one grant after inspecting current policy. `iam_binding_remove {bindingId,organizationId?}` removes the selected explicit grant; inherited access may remain.
- `iam_deny_create {resource,deniedPrincipals,deniedPermissions,exceptionPrincipals?,condition?,reason?,organizationId?}`; iam_deny_update {ruleId,changes}; iam_deny_delete {ruleId}. Inspect existing rules first and retain unrelated conditions/exceptions. Removing a denial can broaden effective access.
- `iam_boundary_set {organizationId,boundary}` changes an organization's permission ceiling. Read the existing boundary and use its schema (including the current etag when required inside boundary); do not guess a preset or permission list.
- `iam_settings_get {organizationId}` / `iam_settings_update {organizationId,membersSeeAllProjects}` controls organization members' project visibility. Review the affected population and current setting before applying it.

Keep authorization, native production prompts and CAS/etag checks. Test effective access after an authorized write, and explain inherited/deny/boundary effects without promising a role label alone changed access.

## Audit and Pai access

- `iam_audit_list {organizationId?,actorId?,action?,before?,limit?}` inspects access changes.
- `iam_pai_access_list {organizationId,before?,limit?}` returns Pai people with access and their activity, roles, expirations and reasons. Follow nextBefore as an opaque cursor unchanged; do not replace it with a timestamp.

Preserve names and IDs from actual responses; do not request extra private data to diagnose access. `examples/access-test.json` is a read-only schema example.
