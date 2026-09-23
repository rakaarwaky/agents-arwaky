"""Check surface — CLI adapter for aa check (AES102 `command` suffix).

All side effects are delegated to the ICheckAggregate; this module stays
free of agent/capability imports (AES205).
"""
from __future__ import annotations

from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.taxonomy_check_vo import CheckExitCode


class CheckAction(ICheckAggregate):
    """CLI action surface for the check feature (surface layer, AES405 aggregate implementor)."""

    def __init__(self, orch: ICheckAggregate) -> None:
        self._orch = orch

    def check(self, strict: bool = False) -> CheckExitCode:
        return self._orch.check(strict=strict)


def cmd_check(args: list[str], orch: ICheckAggregate) -> int:
    """aa check [--strict]."""
    strict = "--strict" in args
    return int(orch.check(strict=strict))

__all__ = ['CheckAction', 'cmd_check']
