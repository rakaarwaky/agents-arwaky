"""Check surface — CLI adapter for aa check (agent-layer verb, AES405)."""
from __future__ import annotations

from modules.check.src.contract_check_aggregate import ICheckAggregate


class CheckVerb(ICheckAggregate):
    """Agent-layer CLI verb surface for the check feature (AES405 aggregate implementor)."""

    def __init__(self, orch: ICheckAggregate) -> None:
        self._orch = orch

    def check(self, strict: bool = False) -> int:
        return self._orch.check(strict=strict)


def cmd_check(args: list[str], orch: ICheckAggregate) -> int:
    """aa check [--strict]."""
    strict = "--strict" in args
    return orch.check(strict=strict)
