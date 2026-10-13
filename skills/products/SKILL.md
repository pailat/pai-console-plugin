---
name: products
description: Productos de un proyecto de Pai Console (las apps que Pai construye u opera) y su ciclo de vida. Cubre alta, estados con aprobación, aprovisionamiento de una Pai App (GitHub + Railway), variables, deploys a staging y producción, dominios, equipo y acceso a producción. Úsalo cuando pidan crear o registrar un producto, aprovisionar, desplegar, configurar variables o dominios, ver logs, dar acceso o pasar un producto a live.
argument-hint: "[proyecto] [producto y acción]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Productos en Pai

Lee antes el skill `pai-console`. Varias de estas tools tocan infraestructura real (GitHub y Railway) y la app que usan los clientes.

**Antes de aprovisionar, desplegar a producción, cambiar variables de producción, conectar un dominio o cambiar el acceso a producción:** di exactamente qué va a pasar y espera el sí explícito de la persona. Esto aplica en cualquier entorno de Console: un deploy desde Console de staging también llega a Railway.

## Lee primero

1. `product_list` (paginado por offset) → `product_get {productId}`.
   - `nextStatus` y `missing[]` dicen qué falta para el siguiente estado.
   - Cada faltante trae su `hint`, con la tool que lo resuelve. **Sigue los `hint`** en vez de adivinar el orden.
2. Si es una Pai App ya aprovisionada:
   - `product_provisioning_get`: pasos, URLs y último deploy;
   - `product_logs {environment, deploymentId?, limit ≤500}`: logs de build o de deploy.

## Estados

`draft` → `building` → `testing` → `live` → `retired`.

- Se piden con `product_request_status {status, note}`; el servidor verifica las compuertas.
- **`live` necesita que otra persona lo apruebe** con `product_decide_status {approve, note}`: quien pidió no puede decidir.
- Desde `retired` solo se vuelve a `draft`, y retirar un producto **no** desaprovisiona nada.

## Alta y aprovisionamiento de una Pai App

1. **`product_create`** con `{name, slug?, description?, type, hosting, recipeKey?, recipeVersion?}`:
   - `type`: `web`, `mobile`, `integration`, `api`, `website` u `other`;
   - `hosting`: `pai` (la operamos en Railway) o `external`;
   - `recipeKey` y `recipeVersion` van juntos o no van;
   - el slug va en inglés; si duplica, da `CONFLICT`.
2. Liga el producto al proyecto: `product_link_project {productId, projectId, role?}` con `role` `creates`, `improves` (por defecto) o `maintains`; religar con otro `role` lo actualiza. Ese vínculo es el que deja usar `productId` en las tools `knowledge_*` desde el proyecto (skill `knowledge`).
3. `product_request_status {status:"building"}`.
4. **`product_provision`** (solo `hosting: pai`), una de dos:
   - `{productId, repositoryName}`: crea el repo privado desde el template;
   - `{productId, repository: "owner/name"}`: usa uno existente tal cual.

   Qué hace:
   - lee el manifiesto `pai.app.json` del repo (permisos, roles, acceso a producción). Sin manifiesto aplica la receta y producción queda **protegida**;
   - crea el proyecto en Railway (Postgres, staging y production, variables, «Entrar con Pai») y el primer deploy de staging.

   **Tiene costo y no se deshace desde el MCP.** Es idempotente: si un paso falla, corrige la causa (por ejemplo, el manifiesto en el repo) y vuelve a llamarla; reanuda sin duplicar.
5. Sigue el avance con `product_provisioning_get` y `product_logs`. No asumas que terminó.

## Variables y deploys

- `product_variables_set {environment, variables, redeploy?}`. **Los valores nunca se devuelven ni se imprimen.**
  - Pide los secretos a la persona en el momento y no los repitas en el chat ni los guardes en pages o nodos.
  - Con `redeploy:true` en producción se vuelve a desplegar el último commit exitoso.
- `product_deploy {environment:"staging"}`: despliega en staging.
- **`product_deploy {environment:"production", commitSha}`** publica ese commit a los usuarios del cliente. El servidor **no** comprueba que el producto esté en `live` ni que el commit pasara por staging. **Compruébalo tú:**
  - el mismo `commitSha` desplegado y verificado en staging (`product_provisioning_get` y `product_logs`);
  - el visto bueno de la persona.
- No hay rollback ni cancelación desde el MCP: un rollback es otro `product_deploy` con el commit anterior bueno.

## Dominios, enlaces y ambientes

| Tool | Qué toca |
|---|---|
| `product_domain_attach {environment, domain}` | **Conecta el dominio en Railway**. Devuelve los `dnsRecords` que la persona debe configurar; llamarla de nuevo re-verifica. No hay herramienta para desconectarlo |
| `product_domain_set` / `_remove` | Solo el registro en la base de datos de Pai |
| `product_environment_set` / `_remove` | Solo el registro en la base de datos de Pai |
| `product_link_set` / `_remove` | Solo el registro en la base de datos de Pai (repositorio, documentación…) |

Quitar un dominio del registro con `product_domain_remove` **no** lo desconecta en Railway.

## Equipo y acceso

- `product_member_list`, y `product_member_add {userId | email, role, appRoles}` / `_update` / `_remove`. El último owner no se puede quitar ni degradar.
- **`product_production_access_set {access}`** (`public` o `protected`):
  - cambia quién puede entrar a la app en producción;
  - actualiza `PAI_PRODUCTION_ACCESS` en Railway y **redespliega producción** si estaba en línea.

  Confirma antes y avisa del redeploy.

## Qué no hacer

- **No** despliegues a producción un commit que no pasó por staging, ni sin el visto bueno de la persona.
- **No** pidas `live` y lo apruebes en la misma sesión como la misma persona: la aprobación es de otra.
- **No** imprimas, registres ni guardes valores de variables o secretos.
- **No** reintentes `product_provision` en bucle: lee `steps[].error`, corrige y llama una vez.
- **No** uses `product_domain_remove` para «desconectar» un dominio: solo borra el registro.
