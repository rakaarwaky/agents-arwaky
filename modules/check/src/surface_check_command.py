"""Check surface — CLI adapter for aa check."""
from __future__ import annotations

from modules.shared.src.check.contract_check_aggregate import ICheckAggregate


def cmd_check(args: list[str], orch: ICheckAggregate) -> int:
    """aa check [--strict]."""
    strict = "--strict" in args
    return orch.check(strict=strict)
