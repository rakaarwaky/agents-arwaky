"""Check agent orchestrator — runs all 5 verification checks in sequence."""
from __future__ import annotations

from modules.check.src.contract_check_aggregate import ICheckAggregate
from modules.check.src.contract_check_protocol import ICheckRunner
from modules.shared.src.utility_logging import banner, err, info, ok


class CheckOrchestrator(ICheckAggregate):
    """Sequence the 5 check capabilities, aggregate their error counts.

    # Block 1: Constructor (capability injection)
    # Block 2: check() sequence
    # Block 3: Result shaping
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, runners: list[ICheckRunner]) -> None:
        self._runners = runners

    # -- Block 2: check() sequence ---------------------------------------------------
    def check(self, strict: bool = False) -> int:
        banner()
        info("Running Python-based repository verification...")
        errors = 0
        print()
        for runner in self._runners:
            errors += runner.run(strict=strict)
        print()
        # -- Block 3: Result shaping ---------------------------------------------------
        if errors:
            err(f"Verification FAILED with {errors} errors.")
            return 1
        ok("All verifications PASSED.")
        return 0
