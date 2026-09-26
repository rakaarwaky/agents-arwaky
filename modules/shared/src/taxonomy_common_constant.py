"""Shared domain constants — taxonomy layer (compile-time only, non-feature).

Merged from: core_constant, paths_constant, version_constant, doc_constant.
(The former the former skill constant file was an exact duplicate of the skill-pack
block here and was removed.)
"""
from __future__ import annotations

import re
from pathlib import Path

# --- skill pack ----------------------------------------------------------------
PROVENANCE_FILE = ".arwaky-skill.json"
PROVENANCE_VERSION = 1
DESCRIPTION_BUDGET_BYTES = 16_200
SKILL_FILE = "SKILL.md"

# --- tool dispatch -------------------------------------------------------------
#: Runner map per tool (manifest-driven dispatch, avoid hardcoded IDs)
TOOL_RUNNERS = {
    "lint-arwaky": "cargo",
    "vision-arwaky": "uv",
    "qwen-web-arwaky": "uv",
    "blender-arwaky": "uv",
}

#: Tool resolver overrides (arg value -> manifest tool id)
INSTALL_OVERRIDES = {
    "workspace": "google-workspace-mcp",
    "fetch": "fetch-mcp",
    "anytype": "anytype-mcp",
    "anytype-daemon": "anytype-mcp",
    "9router": "9router",
}
UNINSTALL_OVERRIDES = {
    "workspace": "google-workspace-mcp",
    "fetch": "fetch-mcp",
    "anytype": "anytype-mcp",
    "9router": "9router",
}

# --- daemons -------------------------------------------------------------------
NINEROUTER_PORT = "20128"
PORT = "20128"

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

# --- doc-pack section contracts & invariant patterns -------------------------
# Pure data/constants shared by the document-invariant pack (utility layer
# may import taxonomy only; these used to live in utility_doc_pack.py).
#: Build/vendored trees that never carry this project's documents.
_SKIP_PARTS = {
    ".git", ".hg", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".venv",
    "__pycache__", "build", "dist", "node_modules", "site-packages", "target", "venv",
    ".worktree", ".worktrees",
}
#: Submodule trees are upstream-owned, so a finding there is noise nobody may act on.
#: ``include_subtrees=True`` opts back in.
_OWNERSHIP_SKIP_DIRS = {"vendor", "internal"}


#: Findings that stay gating even on files the pack merely hosts (upstream ``SKILL.md``
#: copies): a broken pointer is a broken pointer whoever wrote the file.
_ALWAYS_GATING = {"dead-link"}

#: Sections that may exist only in the root master, per references/HOW-TO-MAKE-ROADMAP.md.
MASTER_ONLY_SECTIONS = (
    "State definitions", "Status policy", "Feature roll-up",
    "Branches in flight", "Risk register",
)

#: Headings that hold the runnable commands. Both the section contract and the CI-drift
#: check use this list, so a repo may head that section either way and still be gated.
_COMMANDS_HEADINGS = ("Commands", "Command Reference", "Available Commands",
                      "Available Scripts", "Quick Reference Playbook")

#: Section contract, mirroring references/HOW-TO-MAKE-{prd,roadmap,frd,readme,backlog,agents}.md.
REQUIRED_SECTIONS = {
    "PRD.md": ("Problem Statement", "Goals", "User Personas", "Scope",
               "Feature Requirements", "Non-functional", "Open Questions"),
    "ROADMAP.md": ("Current Condition", "State Definitions", "Status Policy",
                   "Feature Roll-up",
                   "Branches in Flight", "Risk Register"),
    "FRD.md": ("Reference", "System Overview", "Functional Requirements",
               "API Contract", "Integration Points", "Non-functional",
               "Test Scenarios", "Assumptions", "Glossary"),
    "README.md": ("Prerequisites", "Quick Start", "Architecture", "Project Structure",
                  "Available Scripts", "Configuration", "Testing", "Contributing", "License"),
    "AGENTS.md": ("Precedence", "Security", "Commands", "Definition of Done",
                  "Related Documents"),
    "BACKLOG.md": ("Current Condition", "Backlog", "Scenario Evidence", "Blockers",
                   "Dependencies", "Release Readiness", "Deferred", "Change Log"),
}
#: Canonical contract section -> heading fragments that satisfy it. Repos head the same
#: obligation differently, so the check is on the information being present, not on one
#: spelling. The templates in the add-docs references still show the canonical name first.
_SECTION_ALIASES = {
    "Available Scripts": ("Available Scripts", "Available Commands", "Commands",
                          "Developer Workflows", "Orchestrator CLI"),
    "Branches in Flight": ("Branches in Flight", "Branches", "In Flight"),
    "Commands": _COMMANDS_HEADINGS,
    "Configuration": ("Configuration", "Config", "Environment"),
    "Current Condition": ("Current Condition", "Current Status", "Condition"),
    "Definition of Done": ("Definition of Done", "Quality Gates", "Done Criteria",
                           "Verification"),
    "Feature Roll-up": ("Feature Roll-up", "Feature Rollup", "Roll-up", "Rollup"),
    "Glossary": ("Glossary", "Terms", "Definitions"),
    "Open Questions": ("Open Questions", "Open Questions / Risks", "Risks",
                       "Open Questions and Risks"),
    "Precedence": ("Precedence", "Priority Order", "When Documents Disagree"),
    "Project Structure": ("Project Structure", "Repository Structure", "Repo Layout",
                          "Directory Layout", "Architecture Map"),
    "Quick Start": ("Quick Start", "Quickstart", "Getting Started", "Installation"),
    "Related Documents": ("Related Documents", "Reference Paths", "See Also"),
    "Risk Register": ("Risk Register", "Risks"),
    "Scenario Evidence": ("Scenario Evidence", "Evidence"),
    "Security": ("Security", "Guardrails", "Safety"),
    "State Definitions": ("State Definitions", "States", "State Vocabulary"),
    "Status Policy": ("Status Policy", "Verification Policy"),
    "Testing": ("Testing", "Test Suite", "Tests"),
    "Contributing": ("Contributing", "How to Contribute", "Contributor Guide"),
}
#: Sections a harness may legitimately not need, whatever the contract table says.
_SOFT_SECTIONS = {"README.md", "AGENTS.md"}

_COMMITS = re.compile(r"\b[0-9a-f]{7,40}\b")
_CODE_SPAN = re.compile(r"`[^`\n]+`")
_FR_ID = re.compile(r"\bFR-(?:[A-Za-z0-9]+-)?\d+\b")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$", re.MULTILINE)
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")

#: HOW-TO-MAKE-FRD Rule 1: ``FR-<FEATURENAME>-<number>`` (name segment required).
_FR_HEADING = re.compile(r"^#{2,5}\s+(FR-([A-Za-z0-9]+)-(\d+)):\s+(\S.*)$")
#: Loose heading that still looks like an FR but violates Rule 1 / shape.
_FR_HEADING_LOOSE = re.compile(r"^#{2,5}\s+(FR-\S+)")
#: Rule 2 — every requirement states these six fields.
_FR_FIELDS = ("Description", "Input", "Output", "Business Rules", "Edge Cases", "Error Handling")
#: Rule 3 — API Contract column order is exact.
_API_COLUMNS = ("Method", "Input", "Output", "Error", "Event", "Description")
#: Template — Integration Points / Non-functional column contracts.
_INTEGRATION_COLUMNS = ("System", "Direction", "Purpose", "Failure mode")
_NFR_COLUMNS = ("Metric", "Target", "Measurement method")
#: Template section order (HOW-TO-MAKE-FRD § Template).
_FRD_SECTION_ORDER = (
    "Reference", "System Overview", "Functional Requirements",
    "API Contract", "Integration Points", "Non-functional",
    "Test Scenarios", "Assumptions", "Glossary",
)

#: Claims that belong in BACKLOG.md / ROADMAP.md, never in a spec.
_STATUS_LEAKS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*[-*]\s*\[[ xX]\]"), "a checkbox task item"),
    (re.compile(r"^\s*\**\s*status\s*\**\s*:", re.IGNORECASE), "a Status: field"),
    (re.compile(r"\b(?:implemented|unimplemented|partially implemented)\b", re.IGNORECASE),
     "implementation state"),
    (re.compile(r"\b(?:shipped|released|deployed) in v\w*\b", re.IGNORECASE), "release state"),
    (re.compile(r"^\s*(?:✅|❌|🟢|🔴|✔️|✖)"), "a status marker"),
    (re.compile(r"\b\d+\s*%\s*(?:complete|done)", re.IGNORECASE), "a progress percentage"),
)

#: HOW-TO-MAKE-FRD Rule 9 — stateless specs never name source files.
_SOURCE_EXT = re.compile(
    r"(?<![\w.-])(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_.<>{}*-]+\.(?:py|rs|ts|tsx)(?![\w-])"
)

#: Gate binaries a document is allowed to print, used for CI-command drift.
_GATE_COMMANDS = (
    "pytest", "ruff", "mypy", "bandit", "black", "cargo", "clippy", "npm", "pnpm",
    "yarn", "npx", "tsc", "shellcheck", "jq", "make",
)
_ADVISORY = re.compile(r"advisory|not gated|no ci|local only|local-only", re.IGNORECASE)

_ABSOLUTE_PATH = re.compile(
    r"(?<![\w.])/(?:home|users|mnt|volumes|root)/[a-z0-9_.-]+|\bc:\\users",
    re.IGNORECASE,
)
_SECRET_KEY = re.compile(
    r"\b(?:api[_-]?key|secret|token|password|passwd|credential)s?\b\s*[:=]\s*",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"""(?:(?P<q>["'])(?P<quoted>[^"'\s]{8,})(?P=q)|(?P<bare>[A-Za-z0-9_\-./+]{8,}))""",
    re.VERBOSE,
)
#: Values that name a lookup or an obvious stand-in rather than a real secret. Kept
#: case-sensitive so an all-caps env var name is exempt but `hunter2pass` is not.
_PLACEHOLDER_VALUE = re.compile(
    r"^(?:[A-Z][A-Z0-9_]{3,}|<.*>|\$\{?.*|os\.env.*|[Ee]xample.*|[Yy]our.*"
    r"|[Pp]laceholder.*|[Cc]hangeme.*|[Xx]+.*|[Dd]ummy.*|[Ss]ample.*)$"
)


# Dataclasses DocFinding/_Section/Table now live in the shared taxonomy layer
# (taxonomy_common_vo.py); imported at the top of this module.
