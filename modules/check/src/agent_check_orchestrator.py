"""Check agent orchestrator — single-execute aggregate over the check runners.

Resolves each ``CheckRequest.scope`` to the matching protocol method on the
injected runners, then wraps the aggregated gate result in a
``CheckResponse``. Rendering (banner, progress, pass/fail lines) lives on
the surface.
"""
from __future__ import annotations

from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.contract_check_protocol import ICheckProtocol
from modules.shared.src.taxonomy_check_vo import (
    CHECK_SCOPES,
    CheckExitCode,
    CheckRequest,
    CheckResponse,
    CheckScope,
    CheckSummary,
)
from modules.shared.src.taxonomy_common_vo import DocFinding


# ─── Block 1: Class Definition & Constructor ──────────────
class CheckOrchestrator(ICheckAggregate):
    """Single entry point over all repository-verification checks; dispatches internally.

    Scope selection and response assembly live here, so the aggregate keeps
    a single ``execute`` door the surface knocks on.
    """

    def __init__(self, runners: list[ICheckProtocol]) -> None:
        self._runners = runners

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: CheckRequest) -> CheckResponse:
        """Run the runners matching *request*.scope; return the gate response."""
        scope = CheckScope((request.scope or "").strip().lower())
        runners = self._select(scope)
        if not runners:
            return CheckResponse(CheckExitCode(1), CheckSummary("0 findings"))
        errors = 0
        for runner in runners:
            errors += int(runner.run(scope))
        if not errors:
            return CheckResponse(
                CheckExitCode(0), CheckSummary(f"0 findings across {len(runners)} runner(s)")
            )
        return CheckResponse(
            CheckExitCode(1), CheckSummary(f"{errors} error(s) across {len(runners)} runner(s)")
        )

    def summary(self, findings: list[DocFinding]) -> CheckSummary:
        """Collapse *findings* into one digest line."""
        if not findings:
            return CheckSummary("0 findings")
        codes = sorted({finding.code for finding in findings})
        return CheckSummary(
            f"{len(findings)} finding(s) in {len(codes)} code(s): {', '.join(codes)}"
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def _select(self, scope: CheckScope) -> list[ICheckProtocol]:
        """Filter the registered runners by CLI scope; empty/``all`` keeps the full sequence."""
        if not scope:
            return list(self._runners)
        key = CHECK_SCOPES.get(scope)
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
    "CheckRequest",
    "CheckResponse",
    "CheckScope",
    "CheckSummary",
    "DocFinding",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "CheckExitCode": CheckExitCode,
    "CheckRequest": CheckRequest,
    "CheckResponse": CheckResponse,
    "CheckScope": CheckScope,
    "CheckSummary": CheckSummary,
    "DocFinding": DocFinding,
}
