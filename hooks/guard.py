#!/usr/bin/env python3
"""PreToolUse guard for the Pai MCP tools.

Two checks, in this order:

1. Search before create (every environment): a create tool is denied until the
   session has looked for what already exists with a search/list tool of the
   same area. The model reads the reason, searches and tries again.
2. Production (only there): every write asks for confirmation; reads pass. The
   irreversible ones say so and name what they drag along. Nothing is blocked:
   the person decides.

It covers the plugin's server (`mcp__plugin_pai-console_pai__*`, environment from
the plugin's `mcp_url` option) and a user-level `pai-console` server
(`mcp__pai-console__*`, environment from its URL in ~/.claude.json). An unknown
environment counts as production: failing safe means asking once too often.

Reads come from the server's own annotations (hooks/tools.json, generated from
pai-portal 0.2.5+): a tool not in that file counts as a write.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_PREFIX = "mcp__plugin_pai-console_pai__"
USER_PREFIX = "mcp__pai-console__"

STAGING_HOSTS = (
    "mcp-edge-corp-staging.up.railway.app",
    "mcp-corp.paitesting.com",
    "mcp-edge-corp-develop.up.railway.app",
)

TOOLS_FILE = Path(__file__).resolve().parent / "tools.json"


def load_read_tools() -> frozenset[str]:
    """Reads of the corp server, from its own annotations (hooks/tools.json).

    `tools/gen-references.ts` regenerates the file from pai-portal (0.2.5+,
    where every tool declares readOnlyHint). A tool missing from it counts as
    a write, so a new tool asks in production until the file is regenerated.
    """
    try:
        inventory = json.loads(TOOLS_FILE.read_text())
    except (OSError, ValueError):
        return frozenset()
    return frozenset(
        name for name, hints in (inventory.get("tools") or {}).items() if hints.get("readOnly")
    )


READ_TOOLS = load_read_tools()

# Create tool -> tools that count as "looked for what exists first".
SEARCH_BEFORE_CREATE = {
    "page_create": ("page_search", "page_list", "page_read"),
    "note_create": ("page_search", "page_list", "page_read"),
    "knowledge_create": (
        "knowledge_search",
        "knowledge_context",
        "knowledge_library",
        "task_board",
    ),
    "milestone_create": ("timeline_get", "milestone_list"),
    "project_create": ("project_list",),
    "organization_create": ("organization_list",),
    "product_create": ("product_list",),
    "agent_create": ("agent_list",),
    "crm_lead_create": ("crm_lead_duplicates", "crm_lead_list"),
    "crm_opportunity_create": ("crm_organization_get", "crm_opportunity_list"),
}

# Irreversible writes: what the confirmation must say they drag along.
IRREVERSIBLE = {
    "project_delete": "Borra el proyecto con todo lo que depende de él, incluidos pagos y CFDI (borrado en cascada). No hay papelera.",
    "milestone_delete": "Borra el hito; sus CFDI quedan sin hito y su cobro deja de contar. No hay papelera.",
    "page_delete": "Borrado duro: la page, sus versiones, comentarios e índice. page_restore no la recupera; deja backlinks rotos.",
    "payment_void": "Anula el pago para siempre y recalcula el estado de pago de los hitos.",
    "payment_record": "Registra dinero cobrado desde un complemento CFDI P y recalcula el estado de pago de los hitos; solo se corrige anulándolo.",
    "payment_cfdi_import": "Importa un CFDI timbrado al registro fiscal del proyecto; no hay herramienta para editarlo ni borrarlo.",
    "product_deploy": "Despliega en Railway; en production publica ese commit a los usuarios del cliente.",
    "product_variables_set": "Cambia variables de entorno en Railway; con redeploy vuelve a desplegar.",
    "product_production_access_set": "Cambia quién puede entrar a la app en producción y la redespliega si estaba en línea.",
    "product_provision": "Crea el repositorio en GitHub y el proyecto en Railway (Postgres, entornos, despliegue): tiene costo y no se deshace desde el MCP.",
    "product_domain_attach": "Conecta un dominio propio en Railway; no hay herramienta para desconectarlo.",
    "product_member_remove": "Quita a la persona del equipo del producto y de sus roles en la app.",
    "proposal_set_status": "Transición de la propuesta (sent/accepted/rejected) que no se puede revertir.",
    "milestone_baseline_capture": "Congela la línea base del hito; solo se puede capturar una vez.",
    "agent_delete": "Borra el agente del proyecto para siempre (para retirarlo usa status archived).",
    "knowledge_unlink": "Borra la arista entre los nodos.",
    "file_delete": "Borra el archivo de Recursos.",
    "folder_delete": "Borra la carpeta vacía de Recursos con sus subcarpetas vacías; su dirección corta deja de funcionar (404). No se puede deshacer.",
    "asset_delete": "Borra el asset (imagen o video) y su archivo para siempre. Solo si nada lo usa; las versiones viejas que lo citaban muestran su texto alternativo. No se puede deshacer.",
    "crm_lead_purge": "Borra en duro el lead con sus tareas e historial; solo queda una lápida en la auditoría.",
    "crm_opportunity_win": "Gana la oportunidad: fija la propuesta aceptada, convierte el lead, activa la cuenta y pasa el proyecto a planeado.",
}

# High-impact but reversible (or outward-facing) writes.
ATTENTION = {
    "product_request_status": "Pide una transición de estado del producto; desde retired solo se vuelve a draft.",
    "product_decide_status": "Aprueba o rechaza la transición de estado del producto.",
    "status_update_publish": "Publica el estado del proyecto; el cliente lo ve al momento.",
    "knowledge_archive": "Archiva el nodo (reversible con knowledge_revive).",
    "organization_create": "Crea una organización nueva (con ownerEmail envía una invitación).",
    "project_invite_client": "Envía una invitación por correo a la persona del cliente.",
    "crm_lead_create": "Crea el lead y avisa por correo al responsable o al equipo.",
    "crm_lead_qualify": "Califica el lead: siembra nodos en Conocimiento y crea la primera oportunidad.",
    "crm_lead_workspace_open": "Crea o liga la organización del lead y abre su proyecto; no se re-liga después.",
    "crm_lead_workspace_join": "Te agrega como admin de la organización del cliente; queda auditado.",
    "project_close": "Deja el proyecto en solo lectura para todos hasta que se reabra.",
    "project_reopen": "Reabre un proyecto cerrado: vuelve a aceptar escrituras; queda auditado.",
    "note_audience_set": "Con audience client publica la nota para la organización del cliente; internal se la quita.",
    "page_suggestion_decide": "Acepta o rechaza las sugerencias del set; las aceptadas se aplican juntas a la page.",
    "crm_lead_import": "Importa un registro histórico (lead, organización, oportunidad, notas y tareas) con su etapa y fechas reales.",
    "organization_member_remove": "Quita a la persona de la organización del cliente.",
    "organization_member_role_set": "Cambia el rol de una persona en la organización del cliente.",
    "organization_invitation_cancel": "Invalida el enlace de invitación que ya recibió la persona.",
    "organization_slug_set": "Cambia la URL de la organización en el Portal; la anterior redirige y no se puede reutilizar.",
    "project_slug_set": "Cambia la URL del proyecto en el Portal; la anterior redirige.",
    "organization_theme_publish": "Publica el tema de marca; el cliente lo ve en Portal y vistas desde su siguiente carga.",
    "organization_theme_revert": "Vuelve a una versión anterior del tema y, salvo publish: false, la publica al cliente.",
}


def emit(decision: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )


def environment_of_url(url: str | None) -> str:
    if not url:
        return "production"
    return "staging" if any(host in url for host in STAGING_HOSTS) else "production"


def plugin_url() -> str | None:
    """The plugin server's URL: the configured option, else the manifest default.

    Claude Code exports CLAUDE_PLUGIN_OPTION_MCP_URL only once the option has
    been set; until then the server runs on the manifest default, so the hooks
    read that same default instead of guessing.
    """
    url = os.environ.get("CLAUDE_PLUGIN_OPTION_MCP_URL")
    if url:
        return url
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).resolve().parent.parent)
    try:
        manifest = json.loads((Path(root) / ".claude-plugin" / "plugin.json").read_text())
    except (OSError, ValueError):
        return None
    return ((manifest.get("userConfig") or {}).get("mcp_url") or {}).get("default")


def user_server_url() -> str | None:
    """URL of the user-level `pai-console` server, if it is configured there."""
    try:
        config = json.loads((Path.home() / ".claude.json").read_text())
    except (OSError, ValueError):
        return None
    server = (config.get("mcpServers") or {}).get("pai-console") or {}
    return server.get("url")


def tool_environment(tool_name: str) -> tuple[str, str, str] | None:
    """(tool, environment, url) of a Pai tool, or None when it is not one."""
    if tool_name.startswith(PLUGIN_PREFIX):
        url = plugin_url()
        return tool_name[len(PLUGIN_PREFIX) :], environment_of_url(url), url or "?"
    if tool_name.startswith(USER_PREFIX):
        url = user_server_url()
        return tool_name[len(USER_PREFIX) :], environment_of_url(url), url or "?"
    return None


def searched_before(transcript_path: str | None, tools: tuple[str, ...]) -> bool:
    """Whether this session already called one of `tools` on a Pai server."""
    if not transcript_path:
        return True  # nothing to read: never block on a missing transcript
    suffixes = tuple(f"__{tool}" for tool in tools)
    try:
        with open(transcript_path, encoding="utf-8") as transcript:
            for line in transcript:
                if '"tool_use"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                content = (entry.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "tool_use"
                        and str(item.get("name", "")).startswith(
                            (PLUGIN_PREFIX, USER_PREFIX)
                        )
                        and str(item.get("name", "")).endswith(suffixes)
                    ):
                        return True
    except OSError:
        return True
    return False


def summarize(tool_input: dict) -> str:
    keys = (
        "environment",
        "path",
        "newPath",
        "kind",
        "title",
        "name",
        "status",
        "ref",
        "projectId",
        "productId",
        "milestoneId",
        "proposalId",
        "paymentId",
        "id",
    )
    parts = [
        f"{key}={json.dumps(tool_input[key], ensure_ascii=False)}"
        for key in keys
        if key in tool_input and tool_input[key] not in (None, "")
    ]
    return ", ".join(parts)[:300]


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    resolved = tool_environment(str(event.get("tool_name", "")))
    if resolved is None:
        return
    tool, environment, url = resolved
    tool_input = event.get("tool_input") or {}

    if tool in SEARCH_BEFORE_CREATE:
        searches = SEARCH_BEFORE_CREATE[tool]
        if not searched_before(event.get("transcript_path"), searches):
            emit(
                "deny",
                f"Busca antes de crear: en esta sesión no has llamado a {' / '.join(searches)}. "
                "Busca si ya existe (por título, ruta o palabras del tema), reutiliza o actualiza lo que haya "
                f"y solo entonces vuelve a llamar a {tool}.",
            )
            return

    if environment != "production" or tool in READ_TOOLS:
        return

    detail = summarize(tool_input)
    where = f"PRODUCCIÓN ({url})"
    if tool in IRREVERSIBLE or tool in ATTENTION:
        irreversible = tool in IRREVERSIBLE and not (
            tool == "product_deploy" and tool_input.get("environment") != "production"
        )
        severity = "IRREVERSIBLE" if irreversible else "ATENCIÓN"
        consequence = IRREVERSIBLE.get(tool) or ATTENTION[tool]
        emit(
            "ask",
            f"{severity} — {tool} en {where}. {consequence}"
            + (f" Datos: {detail}." if detail else "")
            + " ¿Confirmas?",
        )
        return
    emit(
        "ask",
        f"Escritura en {where}: {tool}"
        + (f" ({detail})" if detail else "")
        + ". ¿Confirmas?",
    )


if __name__ == "__main__":
    main()
