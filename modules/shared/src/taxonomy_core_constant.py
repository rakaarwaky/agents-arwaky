"""Shared constants for the AES tool domains.

Provenance:
- SKILL_PACK_*: modules/skill/src/capabilities_skill_pack.py
- TOOL_RUNNERS: modules/cli/src/root_cli_entry.py
- INSTALL/UNINSTALL_OVERRIDES: modules/runner/src/capabilities_runner.py + modules/shared/src (flat)
- IMAGE_NAME/PORT: tools/daemons/ninerouter_daemon.py
- ANYTYPE_*: modules/mcp/src/capabilities_mcp_generator.py
- DOC/BACKLOG vocabularies: modules/check/src/capabilities_doc_pack.py
"""
from __future__ import annotations

# --- skill pack (was lib/skill_pack.py) ---------------------------------------
PROVENANCE_FILE = ".arwaky-skill.json"
PROVENANCE_VERSION = 1
DESCRIPTION_BUDGET_BYTES = 16_200

# --- tool dispatch (was cli/arwaky.py) ----------------------------------------
# Runner map per tool (P5-P1: manifest-driven dispatch, avoid hardcoded IDs)
TOOL_RUNNERS = {
    "lint": "cargo",
    "vision": "uv",
    "qwen-web": "uv",
    "blender": "uv",
}

# --- tool resolver (was lib/tool_resolver.py) ----------------------------------
INSTALL_OVERRIDES = {
    "workspace": "google-workspace-mcp",
    "fetch": "fetch-mcp",
    "anytype": "anytype-mcp",
    "anytype-daemon": "anytype-mcp",
    "9router": "ninerouter",
}
UNINSTALL_OVERRIDES = {
    "workspace": "google-workspace-mcp",
    "fetch": "fetch-mcp",
    "anytype": "anytype-mcp",
    "9router": "ninerouter",
}

# --- daemons (was daemons/ninerouter_daemon.py) --------------------------------
IMAGE_NAME = "ghcr.io/decolua/9router:latest"
PORT = "20128"

# --- anytype (was mcp/generate_config.py) ---------------------------------------
ANYTYPE_PORT = "31012"
ANYTYPE_BASE_URL = "http://127.0.0.1:31012"

# --- doc pack (was lib/doc_pack.py, copied verbatim) ----------------------------
SPEC_DOCS = ("PRD.md", "FRD.md")
DOC_NAMES = ("PRD.md", "FRD.md", "README.md", "AGENTS.md", "BACKLOG.md")
#: Documents this repo authors; findings on anything else are advisory.
OWNED_DOCS = (*DOC_NAMES, "SKILL.md")

#: The state vocabulary, which lives once in the root master backlog.
STATE_VOCAB = (
    "Idea", "Refinement", "Ready", "In Progress", "Blocked", "In Review",
    "QA", "Done", "Released", "Deferred",
)
HEALTH_VOCAB = (
    "On Track", "At Risk", "Blocked", "Ready for QA", "Ready for Release", "Released",
)
#: States that assert finished work, and therefore owe evidence.
EVIDENCED_STATES = frozenset({"Done", "Released"})

#: Column order a ``Backlog`` table must keep, per references/backlog.md.
BACKLOG_COLUMNS = (
    "ID", "FRD Ref", "Work Item", "Priority", "State",
    "Actual Condition", "Owner", "Dependencies", "Updated",
)
