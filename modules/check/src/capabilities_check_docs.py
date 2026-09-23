"""Docs check capability — delegates to the shared doc_pack domain.

Aligns with the add-docs golden standard under
``skills/documentation/add-docs/references/HOW-TO-MAKE-*.md``:
PRD → ROADMAP (root master) → FRD → feature BACKLOG → README → AGENTS.
"""
from __future__ import annotations

import os
from pathlib import Path

from modules.shared.src.contract_check_protocol import ICheckRunner
from modules.shared.src.taxonomy_check_vo import CheckExitCode
from modules.shared.src.utility_doc_pack import (
    DocFinding,
    as_strict,
    audit_docs,
    errors_only,
    warnings_only,
)
from modules.shared.src.utility_logging_setup import err, info, ok, warn
from modules.shared.src.utility_paths_resolver import repo_root

# ─── Block 1: Class Definition & Constructor ──────────────

class DocsCheckRunner(ICheckRunner):
    """Audit document invariants via the shared doc_pack domain."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def run(self, strict: bool = False) -> CheckExitCode:
        print("[1/2] Validating document invariants (PRD/ROADMAP/FRD/BACKLOG/README/AGENTS)...")
        findings = self.audit(strict=strict)
        problems = errors_only(as_strict(findings)) if strict else errors_only(findings)
        surface = [f for f in warnings_only(findings)
                   if not f.path.startswith(f"{self._root}{os.sep}skills{os.sep}")]
        for finding in problems:
            err(f"{finding.code} {finding.path}: {finding.message}")
        for finding in surface:
            warn(f"{finding.code} {finding.path}: {finding.message}")
        if not findings:
            ok("every document satisfies the add-docs invariants")
        elif not problems:
            ok(f"{len(findings)} advisory finding(s), no errors")
            info("  list them with 'aa docs check'; gate on them with 'aa docs check --strict'")
        return CheckExitCode(len(problems))

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def audit(self, strict: bool = False, include_subtrees: bool = False) -> list[DocFinding]:
        return audit_docs(self._root, include_subtrees=include_subtrees)
