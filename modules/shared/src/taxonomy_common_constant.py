"""Shared domain constants — taxonomy layer (compile-time only, non-feature).

Merged from: core_constant, paths_constant, version_constant, doc_constant.
(The former the former skill constant file was an exact duplicate of the skill-pack
block here and was removed.)
"""
from __future__ import annotations

from pathlib import Path

# --- skill pack ----------------------------------------------------------------
PROVENANCE_FILE = ".arwaky-skill.json"
PROVENANCE_VERSION = 1
DESCRIPTION_BUDGET_BYTES = 16_200
SKILL_FILE = "SKILL.md"

# --- tool dispatch -------------------------------------------------------------
#: Runner map per tool (manifest-driven dispatch, avoid hardcoded IDs)
TOOL_RUNNERS = {
    "lint": "cargo",
    "vision": "uv",
    "qwen-web": "uv",
    "blender": "uv",
}

#: Tool resolver overrides (arg value -> manifest tool id)
INSTALL_OVERRIDES = {
    "workspace": "google-workspace-mcp",
    "fetch": "fetch-mcp",
    "anytype": "anytype-mcp",
    "anytype-daemon": "anytype-mcp",
    "omniroute": "omniroute",
}
UNINSTALL_OVERRIDES = {
    "workspace": "google-workspace-mcp",
    "fetch": "fetch-mcp",
    "anytype": "anytype-mcp",
    "omniroute": "omniroute",
}

# --- daemons -------------------------------------------------------------------
OMNIROUTE_PORT = "7777"
PORT = "7777"

# --- anytype -------------------------------------------------------------------
ANYTYPE_PORT = "31012"
ANYTYPE_BASE_URL = "http://127.0.0.1:31012"

# --- doc pack ------------------------------------------------------------------
SPEC_DOCS = ("PRD.md", "FRD.md")
DOC_NAMES = ("PRD.md", "ROADMAP.md", "FRD.md", "README.md", "AGENTS.md", "BACKLOG.md")
#: Documents this repo authors; findings on anything else are advisory.
OWNED_DOCS = (*DOC_NAMES, "SKILL.md")

#: The state vocabulary, which lives once in the root master (ROADMAP.md).
STATE_VOCAB = (
    "Idea", "Refinement", "Ready", "In Progress", "Blocked", "In Review",
    "QA", "Done", "Released", "Deferred",
)
HEALTH_VOCAB = (
    "On Track", "At Risk", "Blocked", "Ready for QA", "Ready for Release", "Released",
)
#: States that assert finished work, and therefore owe evidence.
EVIDENCED_STATES = frozenset({"Done", "Released"})

#: Column order a ``Backlog`` table must keep, per references/HOW-TO-MAKE-BACKLOG.md.
BACKLOG_COLUMNS = (
    "ID", "FRD Ref", "Work Item", "Priority", "State",
    "Actual Condition", "Owner", "Dependencies", "Updated",
)

# --- filesystem anchors --------------------------------------------------------
#: Repository root (walks up from this file's location: modules/shared/src).
REPO_ROOT: Path = Path(__file__).resolve().parents[3]

#: Provenance marker baked into launcher first lines; foreign files without it are residual.
PROVENANCE_MARKER = "# arwaky-installer"

# --- version -------------------------------------------------------------------
DEFAULT_VERSION = "0.1.0"

# --- document invariants -------------------------------------------------------
ERROR = "error"
WARN = "warning"
