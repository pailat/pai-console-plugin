---
name: pai-env
description: Muestra o cambia el entorno del MCP de Pai del plugin (staging o producción).
argument-hint: "[staging | production]"
disable-model-invocation: true
allowed-tools: Bash(claude plugin configure:*)
---

# Entorno del MCP de Pai

Entorno pedido: `$ARGUMENTS` (vacío = solo mostrar).

URLs del edge corp:

| Entorno | URL |
|---|---|
| staging (por defecto) | `https://mcp-edge-corp-staging.up.railway.app/mcp` |
| production | `https://mcp-corp.pai.lat/mcp` |

1. Muestra el valor actual con `claude plugin configure pai-console --json`.
2. Si no pidieron un cambio, termina diciendo el entorno actual en una línea.
3. Si piden **production**, confirma primero con la persona: en producción cada escritura le pedirá confirmación.
4. Guarda el valor sin imprimir nada más:
   ```bash
   printf '%s' '{"mcp_url":"<URL del entorno>"}' | claude plugin configure pai-console --values-stdin
   ```
5. Dile a la persona que:
   - recargue el plugin o reinicie la sesión;
   - inicie sesión en `/mcp` (servidor `plugin:pai-console:pai`), porque el token es por URL;
   - el aviso de entorno del inicio de sesión mostrará el nuevo.
