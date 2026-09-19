"""Document invariant checks (P3) — capability facade.

Re-exports everything from ``modules.shared.src.utility_doc_pack`` so callers that
already import from ``modules.check.src.capabilities_doc_pack`` keep working
through the refactor without a second import-swap pass.
"""
from __future__ import annotations


import importlib


_doc_pack = importlib.import_module("modules.shared.src.utility_doc_pack")
globals().update({n: getattr(_doc_pack, n) for n in dir(_doc_pack) if not n.startswith("__")})

from modules.shared.src.taxonomy_doc_vo import DocFinding
__all__ = [n for n in dir(_doc_pack) if not n.startswith("__")] + ["DocFinding"]

from modules.check.src.contract_check_protocol import ICheckRunner


# ─── Block 1: Class Definition & Constructor ──────────────
class DocPackRunner(ICheckRunner):
    """Thin wrapper re-exporting shared doc_pack via protocol (keeps legacy import path alive)."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def run(self, strict: bool = False) -> int:
        findings = _doc_pack.audit_docs()
        return len(_doc_pack.errors_only(findings)) if not strict else len(findings)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return "DocPackRunner()"

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DocFinding": DocFinding}
