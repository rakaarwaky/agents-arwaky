"""Check agent orchestrator — runs all 2 verification checks in sequence."""
from __future__ import annotations

from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.contract_check_protocol import ICheckProtocol
from modules.shared.src.taxonomy_check_vo import CheckExitCode, CheckOnly
from modules.shared.src.taxonomy_common_vo import DocFinding
from modules.shared.src.utility_logging_setup import banner, err, info, ok

#: CLI scope aliases → runner ``name`` (surface + orchestrator share this map).
CHECK_SCOPES: dict[str, str] = {
    "all": "",
    "docs": "docs",
    "doc": "docs",
    "skill": "skill",
    "skills": "skill",
}


class CheckOrchestrator(ICheckAggregate):
    """Sequence the check capabilities, aggregate their error counts.

    # Block 1: Constructor (capability injection)
    # Block 2: check() sequence
    # Block 3: Result shaping
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, runners: list[ICheckProtocol]) -> None:
        self._runners = runners

    # -- Block 2: check() sequence ---------------------------------------------------
    def check(self, only: CheckOnly | None = None) -> CheckExitCode:
        banner()
        info("Running Python-based repository verification...")
        runners = self._select(only)
        if not runners:
            err(f"Unknown check scope: {only!r} (expected docs | skill | all)")
            return CheckExitCode(1)
        errors = 0
        total = len(runners)
        print()
        for index, runner in enumerate(runners, 1):
            title = getattr(runner, "title", None) or f"Validating {runner.name}..."
            print(f"[{index}/{total}] {title}")
            errors += int(runner.run())
        print()
        # -- Block 3: Result shaping ---------------------------------------------------
        if errors:
            err(f"Verification FAILED with {errors} errors.")
            return CheckExitCode(1)
        ok("All verifications PASSED.")
        return CheckExitCode(0)

    def _select(self, only: CheckOnly | None) -> list[ICheckProtocol]:
        """Filter *runners* by CLI scope; empty/``all`` keeps the full sequence."""
        if only is None or only == "":
            return list(self._runners)
        key = CHECK_SCOPES.get(only.strip().lower())
        if key is None:
            # Pass through so check() can report the unknown scope.
            return []
        if key == "":
            return list(self._runners)
        return [r for r in self._runners if getattr(r, "name", "") == key]

__all__ = ['CHECK_SCOPES', 'CheckExitCode', 'CheckOnly', 'DocFinding']


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"CheckExitCode": CheckExitCode, "CheckOnly": CheckOnly, "DocFinding": DocFinding}
