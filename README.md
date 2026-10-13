# pai-console

Plugin de Claude Code para que el staff de Pai opere proyectos de clientes en **Pai Console** por su MCP corp. Incluye:

- el MCP ya configurado;
- skills opinados para Recursos, vistas, Conocimiento (ERD, C4, pantallas), Cronograma, Propuestas y Pagos, Productos, CRM y el tema de marca;
- una guarda de escrituras en producción.

## Requisitos

**Pai 0.2.5 en adelante.** Los skills usan sin alternativas lo que llega en 0.2.5:
- `data_model` y C4 por niveles;
- `knowledge_view`, `knowledge_library`, `knowledge_graph` y `task_board`;
- la UI generativa (`view_catalog`, `view_render` y vistas en las lecturas) y el conocimiento propio de la organización;
- las anotaciones de las tools y los errores con `cause`.
- en Recursos, el bloque `html`, los atributos de page con sus filtros, notas, carpetas, sugerencias y `page_projection`;
- comentarios con audiencias (`agent`, `team`, `client`, `person`), el cierre de proyecto y el CRM.

Un entorno con una versión anterior no está soportado: el modelo lo dice y para, sin improvisar. Producción queda soportada cuando corra 0.2.5.

## Instalación

El repo es su propio marketplace (`.claude-plugin/marketplace.json`, marketplace `pai-console-plugin`). Es privado: Claude Code usa tus credenciales de git, así que antes deja `gh` como credencial de HTTPS (`gh auth login` y `gh auth setup-git`).

```
/plugin marketplace add pailat/pai-console-plugin
/plugin install pai-console@pai-console-plugin
```

O desde la terminal:

```bash
claude plugin marketplace add pailat/pai-console-plugin
claude plugin install pai-console@pai-console-plugin
```

Después elige el entorno (`/pai-console:pai-env`) e inicia sesión en `/mcp`.

**Actualizaciones:** `/plugin` detecta una versión nueva por el `version` de `.claude-plugin/plugin.json`; si no cambia, nadie se actualiza. Para un marketplace propio la actualización automática viene apagada: actívala en `/plugin` → Marketplaces, o actualiza con `claude plugin update pai-console@pai-console-plugin` y `/reload-plugins`.

También está en el marketplace del kit de marca (`pai-marketplace`) como `pai-console@pai-marketplace`.

Para probarlo en una sola sesión sin instalarlo:

```bash
claude --plugin-dir ~/Projects/pai/pai-console-plugin/code/pai-console-plugin
```

## Entorno y login

El plugin trae un solo servidor MCP, `pai` (`plugin:pai-console:pai`). Su URL sale de la opción `mcp_url` del plugin:

| Entorno | URL | Authorization server |
|---|---|---|
| **staging** (por defecto) | `https://mcp-edge-corp-staging.up.railway.app/mcp` | Console de staging |
| develop (sin guarda de producción) | `https://mcp-edge-corp-develop.up.railway.app/mcp` | Console de develop |
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
| `PreToolUse` · buscar antes de crear (`hooks/guard.py`) | Rechaza `page_create`, `note_create`, `knowledge_create`, `milestone_create`, `project_create`, `organization_create`, `product_create` y `agent_create` si en la sesión no hubo antes una búsqueda o un listado de su área. El modelo lee el motivo, busca y reintenta. Evita duplicados, el error más caro de deshacer en el grafo. |

La guarda sabe qué es lectura por las anotaciones del propio servidor. Las lee de `hooks/tools.json`, que `tools/gen-references.ts` genera construyendo el servidor MCP de pai-portal en memoria. Una tool que no está en ese archivo cuenta como escritura hasta que se regenere.

### Skills

| Skill | Para |
|---|---|
| `pai-console` | El método base: entorno, descubrimiento, buscar antes de crear, CAS, idempotencia, nombres en inglés, errores, citas. Con el inventario de tools (también el tema de la organización, con su `shell`) |
| `resources` | Pages con tipo, bloques `view`, `html` (mockups y prototipos interactivos) y `projection`, atributos (fecha, responsable, estatus, etiquetas) y filtros, notas, carpetas, sugerencias, comentarios con audiencias y anclas, imágenes, archivos, mover, restaurar y borrar |
| `views` | UI generativa de Pai (`pai-view@1`, 150 componentes, patrones con regiones y 68 recetas del servidor): `view_render` para dibujar en la conversación; layouts reales de Portal, Console, pai.lat y login; piezas de datos del Portal (Pagos, Cronograma, Tareas, Proyectos, Actividad, Biblioteca); diagramas ERD/C4 y grafo; tableros, mockups, reportes visuales y comparativos guardados en Recursos. Recetas validadas y catálogo generado |
| `knowledge` | Kinds, fuentes, propuestas que confirma una persona, enlaces por ontología (incluido `implemented_by`), conocimiento de producto (`productId`), `knowledge_query`, `knowledge_batch`, ciclo de vida |
| `erd` | `data_model` + `entity`: columnas tipadas; las relaciones salen de las FK |
| `c4` | `component` por nivel y `actor`; relaciones con descripción y tecnología |
| `screens` | `screen`, `flow`, `actor` |
| `schedule` | Hitos, dependencias, tareas, línea base, tablero, cierre y reapertura del proyecto |
| `proposals-payments` | SOW, estados, CFDI, pagos, anulación |
| `theme` | Tema de marca de una organización (Ajustes › Apariencia, staff): colores claro y oscuro, fuente, radio, sombra, logos y el app shell del Portal; contraste AA, borrador, vista previa, publicar y volver |
| `crm` | CRM de Console (staff o roles de CRM): leads sin duplicados, contacto, calificación, espacio de trabajo, oportunidades por etapa, pausa, pérdida, ganar, interlocutores, probabilidad y pronóstico por moneda |
| `products` | Alta, estados, aprovisionamiento, deploys, variables, dominios, acceso |
| `pai-env` | `/pai-console:pai-env [staging\|develop\|production]`: ver o cambiar el entorno (solo manual) |

Todos los skills de área se pueden invocar como comando (`/pai-console:erd`, `/pai-console:c4`, `/pai-console:resources`, `/pai-console:views`…) o los carga el modelo cuando la tarea encaja.

### Agentes

- `pai-explorer` es de solo lectura: hace búsquedas y lecturas pesadas (catálogos, inventarios, contexto, CRM) sin llenar el contexto principal.
- `theme-designer` propone o corrige el tema de una organización desde una marca o un logo. Itera `organization_theme_preview` hasta pasar AA y devuelve el JSON. Solo lee y previsualiza: guardar y publicar los hace el agente principal con confirmación.

## Desarrollo

Requiere un checkout de pai-portal con dependencias, por ejemplo un worktree detached de la rama que sirve develop (hoy `feat/0.2.5/reui`).

```bash
# Regenerar desde pai-portal: referencias (kinds, ontología, catálogo de vistas, tipos de page),
# hooks/tools.json (inventario y anotaciones de las tools) y evals/mocks/pai/_tools.json
PAI_PORTAL=~/worktrees/pai-console-plugin-ref bun tools/gen-references.ts

# Validar cada ejemplo de los skills contra los esquemas reales
PAI_PORTAL=~/worktrees/pai-console-plugin-ref bun tools/validate-examples.ts

# Tests de los hooks
python3 -m unittest discover -s tests

# Marketplace, manifiesto, skills y agente
claude plugin validate --strict .
claude plugin validate --strict .claude-plugin/plugin.json
claude plugin validate --strict skills
claude plugin validate --strict agents

# Evals del comportamiento contra el MCP simulado (evals/mocks/pai, con el tools/list real de 0.2.5)
claude plugin eval . --allow-tools 'mcp__plugin_pai-console_pai__*' --trust-plugin --no-publish -j 4
```

Las referencias en `skills/*/references/` marcadas «Generado por» no se editan a mano.

## Pendientes en el servidor

Los pedidos al agente `mcp` (anotaciones, errores estructurados, `knowledge_view` duplicada, etc.) están en el diagnóstico del proyecto: `local/PEDIDOS-mcp.md`.
