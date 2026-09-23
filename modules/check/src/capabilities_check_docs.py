"""Docs check capability — delegates to the shared doc_pack domain.

Aligns with the add-docs golden standard under
``skills/documentation/add-docs/references/HOW-TO-MAKE-*.md``:
PRD → ROADMAP (root master) → FRD → feature BACKLOG → README → AGENTS.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_check_protocol import ICheckProtocol
from modules.shared.src.taxonomy_check_vo import CheckExitCode
from modules.shared.src.utility_doc_pack import (
    DocFinding,
    audit_docs,
    errors_only,
)
from modules.shared.src.utility_logging_setup import err, ok
from modules.shared.src.utility_paths_resolver import repo_root

# ─── Block 1: Class Definition & Constructor ──────────────

class DocsCheckRunner(ICheckProtocol):
    """Audit document invariants via the shared doc_pack domain."""

    #: CLI key for ``aa check docs``.
    name = "docs"
    #: Progress line printed by the orchestrator (step index is prefixed there).
    title = "Validating document invariants (PRD/ROADMAP/FRD/BACKLOG/README/AGENTS)..."

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def run(self) -> CheckExitCode:
        findings = self.audit()
        problems = errors_only(findings)
        for finding in problems:
            err(f"{finding.code} {finding.path}: {finding.message}")
        if not findings:
            ok("every document satisfies the add-docs invariants")
        return CheckExitCode(len(problems))

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def audit(self, include_subtrees: bool = False) -> list[DocFinding]:
        return audit_docs(self._root, include_subtrees=include_subtrees)
