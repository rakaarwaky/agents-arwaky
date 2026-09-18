"""Docs check capability — delegates to the shared doc_pack domain."""
from __future__ import annotations

import os
from pathlib import Path

from modules.check.contract.contract_check_protocol import ICheckRunner
from modules.shared.src.doc_pack.capabilities_doc_pack import (
    DocFinding,
    as_strict,
    audit_docs,
    errors_only,
    warnings_only,
)
from modules.shared.src.logging.utility_logging import err, info, ok, warn
from modules.shared.src.paths.utility_paths import repo_root


class DocsCheckRunner(ICheckRunner):
    """Audit document invariants via the shared doc_pack domain.

    # Block 1: Configuration
    # Block 2: Audit
    # Block 3: Report
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    # -- Block 2: Audit ------------------------------------------------------------
    def audit(self, strict: bool = False, include_subtrees: bool = False) -> list[DocFinding]:
        return audit_docs(self._root, include_subtrees=include_subtrees)

    # -- Block 3: Report ------------------------------------------------------------
    def run(self, strict: bool = False) -> int:
        print("[3/5] Validating document invariants...")
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
        return len(problems)
