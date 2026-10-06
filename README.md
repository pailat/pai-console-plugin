# pai-console

Plugin de Claude Code para que el staff de Pai opere proyectos de clientes en **Pai Console** por su MCP corp. Incluye:

- el MCP ya configurado;
- skills opinados para Recursos, Conocimiento (ERD, C4, pantallas), Cronograma, Propuestas y Pagos, y Productos;
- una guarda de escrituras en producción.

## Instalación

Desde el marketplace de Pai:

```
/plugin marketplace add <ruta o repo del marketplace>
/plugin install pai-console@<marketplace>
```

Para probarlo en una sola sesión sin instalarlo:

```bash
claude --plugin-dir ~/Projects/pai/pai-console-plugin/code/pai-console-plugin
```

## Entorno y login

El plugin trae un solo servidor MCP, `pai` (`plugin:pai-console:pai`). Su URL sale de la opción `mcp_url` del plugin:

| Entorno | URL | Authorization server |
|---|---|---|
| **staging** (por defecto) | `https://mcp-edge-corp-staging.up.railway.app/mcp` | Console de staging |
| producción | `https://mcp-corp.pai.lat/mcp` | `https://console.pai.lat` |

**Cambiar de entorno**, por cualquiera de estas vías:
- `/pai-console:pai-env production`;
- `/plugin` → pai-console → configurar;
- `printf '%s' '{"mcp_url":"https://mcp-corp.pai.lat/mcp"}' | claude plugin configure pai-console --values-stdin`.

**Login:** en `/mcp` elige `plugin:pai-console:pai` → *Authenticate*.
- Es OAuth 2.1 con registro dinámico y PKCE contra Console, con scope `pai:manage`. Inicia sesión con tu cuenta de staff de Pai.
- El token es por URL: al cambiar de entorno, vuelve a iniciar sesión.
- Solo el staff que sea miembro de la organización ve y usa sus proyectos.

## Qué hace cada pieza

### Hooks

| Hook | Por qué |
|---|---|
| `SessionStart` (`hooks/session_start.py`) | Dice a la persona y al modelo en qué entorno está el MCP y qué tools usar. Si también existe el servidor de usuario `pai-console`, avisa a qué entorno apunta. Evita escribir en producción creyendo que es staging. |
| `PreToolUse` · producción (`hooks/guard.py`) | En producción **cada escritura pide confirmación**; las lecturas pasan libres. Las irreversibles (`project_delete`, `page_delete`, `payment_void`, `product_deploy` a production…) lo dicen y nombran qué arrastran. No bloquea nada: decide la persona. En staging no pregunta. Cubre las tools del plugin y las del servidor de usuario `pai-console`, cuyo entorno se deduce de su URL. |
| `PreToolUse` · buscar antes de crear (`hooks/guard.py`) | Rechaza `page_create`, `knowledge_create`, `milestone_create`, `project_create`, `organization_create`, `product_create` y `agent_create` si en la sesión no hubo antes una búsqueda o un listado de su área. El modelo lee el motivo, busca y reintenta. Evita duplicados, el error más caro de deshacer en el grafo. |

Las lecturas se listan una por una en `hooks/guard.py` porque el servidor no anota todas sus tools (pedido M2 al agente `mcp`). Una tool desconocida cuenta como escritura.

### Skills

| Skill | Para |
|---|---|
| `pai-console` | El método base: entorno, descubrimiento, buscar antes de crear, CAS, idempotencia, nombres en inglés, errores, citas. Con el inventario de tools |
| `resources` | Pages con tipo, vistas `pai-view@1` (canvas + bloque `view`), imágenes, archivos |
| `knowledge` | Kinds, fuentes, propuestas que confirma una persona, enlaces por ontología, ciclo de vida |
| `erd` | `data_model` + `entity`: columnas tipadas; las relaciones salen de las FK |
| `c4` | `component` por nivel y `actor`; relaciones con descripción y tecnología |
| `screens` | `screen`, `flow`, `actor` |
| `schedule` | Hitos, dependencias, tareas, línea base, tablero |
| `proposals-payments` | SOW, estados, CFDI, pagos, anulación |
| `products` | Alta, estados, aprovisionamiento, deploys, variables, dominios, acceso |
| `pai-env` | `/pai-console:pai-env [staging\|production]`: ver o cambiar el entorno (solo manual) |

Todos los skills de área se pueden invocar como comando (`/pai-console:erd`, `/pai-console:c4`, `/pai-console:resources`…) o los carga el modelo cuando la tarea encaja.

### Agente

`pai-explorer` es de solo lectura: hace búsquedas y lecturas pesadas (catálogos, inventarios, contexto) sin llenar el contexto principal.

## Desarrollo

Requiere un checkout de pai-portal con dependencias, por ejemplo un worktree detached de `release/0.2.5`.

```bash
# Regenerar las referencias desde los contratos (kinds, ontología, vistas, tipos de page)
PAI_PORTAL=~/worktrees/pai-console-plugin-ref bun tools/gen-references.ts

# Validar cada ejemplo de los skills contra los esquemas reales
PAI_PORTAL=~/worktrees/pai-console-plugin-ref bun tools/validate-examples.ts

# Tests de los hooks
python3 -m unittest discover -s tests

# Manifiesto y estructura del plugin
claude plugin validate --strict .

# Evals del comportamiento contra el MCP simulado (evals/mocks/pai, con el tools/list real de 0.2.5)
claude plugin eval . --allow-tools 'mcp__plugin_pai-console_pai__*' --trust-plugin --no-publish -j 4
```

Las referencias en `skills/*/references/` marcadas «Generado por» no se editan a mano.

## Pendientes en el servidor

Los pedidos al agente `mcp` (anotaciones, errores estructurados, `knowledge_view` duplicada, etc.) están en el diagnóstico del proyecto: `local/PEDIDOS-mcp.md`.
