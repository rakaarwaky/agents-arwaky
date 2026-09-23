"""Check agent orchestrator — runs all 2 verification checks in sequence."""
from __future__ import annotations

from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.contract_check_protocol import ICheckProtocol
from modules.shared.src.taxonomy_check_vo import (
    CHECK_SCOPES,
    CheckExitCode,
    CheckOnly,
    CheckScope,
    CheckSummary,
)
from modules.shared.src.taxonomy_common_vo import DocFinding


# ─── Block 1: Class Definition & Constructor ──────────────
class CheckOrchestrator(ICheckAggregate):
    """Sequence the check capabilities, aggregate their error counts.

    Rendering (banner, progress, pass/fail lines) lives on the surface.
    """

    def __init__(self, runners: list[ICheckProtocol]) -> None:
        self._runners = runners

    # ─── Block 2: Aggregate Method Implementation ──────────
    def check(self, only: CheckOnly | None = None) -> CheckExitCode:
        scope = (only or "").strip().lower() or "all"
        runners = self._select(only)
        if not runners:
            return CheckExitCode(1)
        errors = 0
        for runner in runners:
            errors += int(runner.execute(CheckScope(scope)))
        return CheckExitCode(1 if errors else 0)

    def check_docs(self) -> CheckExitCode:
        """Run only the document-invariant audit."""
        return self.check(CheckOnly("docs"))

    def check_skill(self) -> CheckExitCode:
        """Run only the skill-pack audit."""
        return self.check(CheckOnly("skill"))

    def summary(self, findings: list[DocFinding]) -> CheckSummary:
        """Collapse *findings* into one digest line."""
        if not findings:
            return CheckSummary("0 findings")
        codes = sorted({finding.code for finding in findings})
        return CheckSummary(
            f"{len(findings)} finding(s) in {len(codes)} code(s): {', '.join(codes)}"
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def _select(self, only: CheckOnly | None) -> list[ICheckProtocol]:
        """Filter *runners* by CLI scope; empty/``all`` keeps the full sequence."""
        if only is None or only == "":
            return list(self._runners)
        key = CHECK_SCOPES.get(only.strip().lower())
        if key is None:
            return []
        if key == "":
            return list(self._runners)
        return [r for r in self._runners if getattr(r, "name", "") == key]

    def __repr__(self) -> str:
        return "CheckOrchestrator()"


__all__ = [
    "CHECK_SCOPES",
    "CheckExitCode",
    "CheckOnly",
    "CheckScope",
    "CheckSummary",
    "DocFinding",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "CheckExitCode": CheckExitCode,
    "CheckOnly": CheckOnly,
    "CheckScope": CheckScope,
    "CheckSummary": CheckSummary,
    "DocFinding": DocFinding,
}
