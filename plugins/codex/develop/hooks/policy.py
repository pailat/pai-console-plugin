"""Shared Pai domain policy; client adapters own approvals and session evidence."""

from __future__ import annotations

import json
from pathlib import Path

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
    if not isinstance(inventory, dict) or not isinstance(inventory.get("tools"), dict):
        return frozenset()
    return frozenset(
        name for name, hints in inventory["tools"].items()
        if isinstance(hints, dict) and hints.get("readOnly") is True
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
    "flow_create": ("flow_list", "flow_get", "knowledge_search", "knowledge_library"),
}

# Irreversible writes: what the confirmation must say they drag along.
IRREVERSIBLE = {
    "project_delete": "Permanently deletes the project and all dependent records, including payments and CFDI (cascade deletion). There is no trash.",
    "milestone_delete": "Permanently deletes the milestone; its CFDI lose their milestone and their payments no longer count. There is no trash.",
    "page_delete": "Hard deletes the page, versions, comments, and index. page_restore cannot recover it; backlinks break.",
    "payment_void": "Permanently voids the payment and recalculates milestone payment status.",
    "payment_record": "Records collected money from a CFDI P supplement and recalculates milestone payment status; corrections require voiding it.",
    "payment_cfdi_import": "Imports a stamped CFDI into the project fiscal registry; no tool can edit or delete it.",
    "product_deploy": "Deploys to Railway; production publishes that commit to client users.",
    "product_variables_set": "Changes Railway environment variables; redeploy triggers another deployment.",
    "product_production_access_set": "Changes production app access and redeploys the app if it was online.",
    "product_provision": "Creates the GitHub repository and Railway project (Postgres, environments, deployment): incurs costs and cannot be undone through MCP.",
    "product_domain_attach": "Attaches a custom domain in Railway; no tool can detach it.",
    "product_member_remove": "Removes the person from the product team and their app roles.",
    "proposal_set_status": "Irreversible proposal transition (sent/accepted/rejected).",
    "milestone_baseline_capture": "Freezes the milestone baseline; it can only be captured once.",
    "agent_delete": "Permanently deletes the project agent (use status archived to retire it).",
    "knowledge_unlink": "Deletes the edge between the nodes.",
    "file_delete": "Deletes the file from Resources.",
    "folder_delete": "Permanently deletes the empty Resources folder and its empty subfolders; its short URL stops working (404). This cannot be undone.",
    "asset_delete": "Permanently deletes the asset (image or video) and its file if unused; older versions referencing it show its alternative text. This cannot be undone.",
    "crm_lead_purge": "Hard deletes the lead, tasks, and history; only an audit tombstone remains.",
    "crm_opportunity_win": "Wins the opportunity: fixes the accepted proposal, converts the lead, activates the account, and moves the project to planned.",
}

# High-impact but reversible (or outward-facing) writes.
ATTENTION = {
    "product_request_status": "Requests a product status transition; retired can only return to draft.",
    "product_decide_status": "Approves or rejects the product status transition.",
    "status_update_publish": "Publishes the project status to the client immediately.",
    "knowledge_archive": "Archives the node (reversible with knowledge_revive).",
    "organization_create": "Creates an organization (ownerEmail sends an invitation).",
    "project_invite_client": "Emails an invitation to the client contact.",
    "crm_lead_create": "Creates the lead and emails the owner or team.",
    "crm_lead_qualify": "Qualifies the lead: seeds Knowledge nodes and creates the first opportunity.",
    "crm_lead_workspace_open": "Creates or links the lead organization and opens its project; it cannot be relinked later.",
    "crm_lead_workspace_join": "Adds you as an admin of the client organization; the action is audited.",
    "project_close": "Makes the project read-only for everyone until reopened.",
    "project_reopen": "Reopens a closed project for writes; the action is audited.",
    "note_audience_set": "audience client publishes the note to the client organization; internal removes that access.",
    "page_suggestion_decide": "Accepts or rejects the suggestion set; accepted suggestions are applied together to the page.",
    "crm_lead_import": "Imports a historical record (lead, organization, opportunity, notes, and tasks) with its actual stage and dates.",
    "organization_member_remove": "Removes the person from the client organization.",
    "organization_member_role_set": "Changes a person's role in the client organization.",
    "organization_invitation_cancel": "Invalidates the invitation link already received by the person.",
    "organization_slug_set": "Changes the organization URL in Portal; the old URL redirects and cannot be reused.",
    "project_slug_set": "Changes the project URL in Portal; the old URL redirects.",
    "organization_theme_publish": "Publishes the brand theme to Portal and views on the client's next load.",
    "organization_theme_revert": "Restores a previous theme version and publishes it to the client unless publish: false.",
}
