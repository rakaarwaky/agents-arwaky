"""Harness-domain protocol contract (single capability ABC).

Exactly one class + one method: ``execute(op, targets, flags?)`` covers
connect, disconnect, and skill provisioning (FRD Protocol API). All three
capabilities implement this same protocol. Adapters are stateless utility
leaves (duck-typed objects) — they are not contract protocols.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_harness_vo import ExitCode, HarnessFlags, HarnessOp, HarnessTargets


class IHarnessProtocol(ABC):
    """Single capability method covering connect / disconnect / provision.

    FR-HARNESS-001, FR-HARNESS-002, and FR-HARNESS-003 dispatch through
    *op* (``connect`` | ``disconnect`` | ``provision_skills``) over
    resolved *targets*, with an optional *flags* bag.
    """

    @abstractmethod
    def execute(self, op: HarnessOp, targets: HarnessTargets,
                flags: HarnessFlags | None = None) -> ExitCode:
        """Run *op* over *targets*; return exit code (0 = success)."""
        ...


__all__ = ["ExitCode", "HarnessFlags", "HarnessOp", "HarnessTargets", "IHarnessProtocol"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "HarnessFlags": HarnessFlags,
    "HarnessOp": HarnessOp,
    "HarnessTargets": HarnessTargets,
    "IHarnessProtocol": IHarnessProtocol,
}
