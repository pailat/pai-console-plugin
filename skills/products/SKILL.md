---
name: products
description: "Manage Pai Console project products and lifecycle: registration, approval-gated states, Pai App provisioning (GitHub/Railway), variables, staging/production deploys, domains, team, and production access. Use to register, provision, deploy, configure, inspect logs, grant access, or move a product to live."
argument-hint: "[project] [product and action]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Products in Pai

Read shared `pai-console` first through the current client's skill mechanism. Several tools change real GitHub/Railway infrastructure and client applications.

**Before provisioning, production deploys, production variable changes, domain attachment, or production access changes:** explain exactly what will happen and wait for explicit user approval. This applies in every Console environment: staging Console deploys also reach Railway.

## Read first

1. Offset-paginated `product_list` → `product_get {productId}`.
   - `nextStatus` and `missing[]` identify next-state prerequisites.
   - Each missing item has a `hint` naming its tool. **Follow hints** rather than guessing order.
2. For an already provisioned Pai App:
   - `product_provisioning_get`: steps, URLs, latest deployment;
   - `product_logs {environment, deploymentId?, limit ≤500}`: build/deploy logs.

## States

`draft` → `building` → `testing` → `live` → `retired`.

- Request with `product_request_status {status, note}`; server checks gates.
- **Definition review before `building`** (advisory). For a `draft` product, staff see `product_get.definition {target:"building", mode:"advisory", ready, checks[], evidence}`. Each check has `code`, `state` (`met`, `unmet`, `info`), `message` and `hint`: `definition_project_required`, `definition_prd_required`, `definition_requirements_agreed`, `definition_prd_confirmed`, `definition_flow_tested`, and the informational `definition_open_questions`. `evidence` lists projects, the PRD (`pageId`, `revision`, requirements, agreed, `confirmation` or null), flow runs and open questions.
  - The review never blocks `missing[]`, the request or the decision. Before requesting `building`, report every `unmet` check with its hint and let the user decide whether to request anyway; the request records a copy of the review in the product's history.
  - Resolve gaps through their own workflows: PRD in `../resources/SKILL.md`, agreed requirements in `../knowledge/SKILL.md`, flow tests in `../flows/SKILL.md`. **`definition_prd_confirmed` is met only when a person confirms the PRD version** in Portal or Console; an agent cannot.
- **`live` requires another person's approval** via `product_decide_status {approve, note}`; requester cannot decide.
- `retired` can return only to `draft`; retirement **does not** deprovision anything.

## Register and provision a Pai App

1. **`product_create`** `{name, slug?, description?, type, hosting, recipeKey?, recipeVersion?}`:
   - `type`: `web`, `mobile`, `integration`, `api`, `website`, `other`;
   - `hosting`: `pai` (operated on Railway) or `external`;
   - `recipeKey` and `recipeVersion`: both present or absent;
   - English slug; duplicates yield `CONFLICT`.
2. `product_link_project {productId, projectId, role?}`: `creates`, `improves` (default), `maintains`; relinking updates `role`. This enables project `knowledge_*` tools with `productId` (`knowledge`).
3. `product_request_status {status:"building"}`.
4. **`product_provision`** (`hosting: pai` only), either:
   - `{productId, repositoryName}` creates a private template repository;
   - `{productId, repository: "owner/name"}` uses an existing repository unchanged, only where the user's scope permits (`pai-console` organization-staff restriction).

   It reads repo `pai.app.json` (permissions, roles, production access). Without a manifest, recipe defaults apply and production is **protected**. It creates a Railway project (Postgres, staging/production, variables, Pai sign-in) and first staging deploy.

   **Costs money and cannot be undone through MCP.** Idempotent: fix a failed step's cause (such as repo manifest) then call again; it resumes without duplicates.
5. Track with `product_provisioning_get` and `product_logs`; never assume completion.

## Variables and deployments

- `product_variables_set {environment, variables, redeploy?}`. **Never return or print values.** Request secrets when needed; never repeat them in chat or store in pages/nodes. `redeploy:true` in production redeploys the last successful commit.
- `product_deploy {environment:"staging"}` deploys staging.
- **`product_deploy {environment:"production", commitSha}`** publishes that commit to client users. Server **does not verify** `live` state or staging history. **Verify yourself:** the same `commitSha` was deployed and verified in staging (`product_provisioning_get`, `product_logs`), and the user approved.
- No MCP rollback/cancel tool: rollback means another `product_deploy` using the previous good commit.

## Domains, links, environments

| Tool | Effect |
|---|---|
| `product_domain_attach {environment, domain}` | **Attaches in Railway**; returns user-configurable `dnsRecords`; repeat to reverify. No detach tool |
| `product_domain_set` / `_remove` | Pai database records only |
| `product_environment_set` / `_remove` | Pai database records only |
| `product_link_set` / `_remove` | Pai database records only (repository, docs…) |

`product_domain_remove` **does not detach** a Railway domain.

## Release plans (internal)

A release plan is an internal, staff-only planned version of a product: a `label` (≤120, unique per product), optional `notes` (≤2000), a product `environmentId` and 1–100 milestones `[{projectId, milestoneId}]` from projects linked to the product. Its status is always `planned`. **It never publishes, deploys or notifies anyone**; deploys stay in the section above.

- `product_release_plan_list {organizationId, productId, limit?, offset?}` first (offset pagination with `total`); reuse a plan with the same purpose instead of creating another.
- `product_release_plan_create {organizationId, productId, label, environmentId, milestones, notes?}` is not idempotent: create once after the user agrees. Take `environmentId` from `product_get` and milestones from `milestone_list` of each linked project; an environment of another product or an unlinked milestone is reported as missing.
- `product_release_plan_update {organizationId, productId, releaseId, expectedRevision, label?, environmentId?, notes?, milestones?}` needs at least one change. Omitting `milestones` keeps them; sending them **replaces the whole set**, so start from the listed set.
- Permissions: product update (read for list) plus `schedule.milestones.update` on every milestone added or removed. Errors: `RELEASE_PLANS_STAFF_ONLY` (also under impersonation), `RELEASE_LABEL_EXISTS` (pick the existing plan or ask for another label), `RELEASE_REVISION_CONFLICT` with `cause.current.revision` (reread and reconcile; never retry automatically), `RELEASE_MILESTONES_REQUIRED`, `RELEASE_REVISION_EXHAUSTED`.

## Team and access

- `product_member_list`; `product_member_add {userId | email, role, appRoles}` / `_update` / `_remove`. Cannot remove/demote the last owner.
- **`product_production_access_set {access}`** (`public`, `protected`) changes production app access, updates Railway `PAI_PRODUCTION_ACCESS`, and **redeploys production** if already online. Confirm first and disclose the redeploy.

## Product work and architecture

Use `../tasks/SKILL.md` for task_list {section:"product",productId} and product-first contexts; filter by productId to include project tasks working on that product. A project task may link to one of its organization's products; a product backlog task cannot change products.

Use `../knowledge/SKILL.md` for product-scoped architecture, cross-scope lookup, atomic subtree movement and deduplication. knowledge_view {view:"c4",productId} without scope renders the product context; product linkage does not grant cross-organization access.

product_update accepts recipeKey and recipeVersion. Hosting/class changes are allowed only in draft before provisioning; changing to external removes the recipe. Read product_get and actual permissions before applying this change; do not provision infrastructure as a workaround for a rejected update.

## Avoid

- Never deploy an unverified staging commit to production or deploy without user approval.
- Never request and approve `live` as the same person/session; another person must approve.
- Never print, log, or store secrets/variable values.
- Never loop `product_provision`; inspect `steps[].error`, correct, then call once.
- Never use `product_domain_remove` as domain disconnection; it only removes a record.
