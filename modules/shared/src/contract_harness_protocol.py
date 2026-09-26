"""Harness-domain protocol contract (rich capability ABC).

Every operation the harness capabilities expose is a named method with its
own typed signature. Capabilities implement the whole protocol; an op they
do not own is ``NotImplementedError``. Adapters are stateless leaf provider
leaves — they implement the protocol with ``NotImplementedError`` bodies for
all three operations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_harness_vo import (
    ExitCode,
    HarnessTargets,
)


class IHarnessProtocol(ABC):
    """Capability contract for harness operations: connect, disconnect, provision_skills.

    FR-HARNESS-001, FR-HARNESS-002, and FR-HARNESS-003 are one named method
    each. Every capability (HarnessConnector, HarnessDisconnector, HarnessSkills)
    implements the whole protocol; an op it does not own is
    ``NotImplementedError``.
    """

    @abstractmethod
    def connect(self, targets: HarnessTargets, force: bool, dry_run: bool,
                mcp_only: bool, skills_only: bool, env_only: bool,
                router: bool, copy_skills: bool) -> ExitCode:
        """FR-001: connect to the resolved harness targets; return exit code."""
        ...

    @abstractmethod
    def disconnect(self, targets: HarnessTargets, dry_run: bool) -> ExitCode:
        """FR-002: disconnect from the resolved harness targets; return exit code."""
        ...

    @abstractmethod
    def provision_skills(self, targets: HarnessTargets, copy: bool, dry_run: bool,
                         force: bool = False) -> ExitCode:
        """FR-003: provision the skill pack into the resolved harness targets; return exit code."""
        ...


__all__ = ["ExitCode", "IHarnessProtocol", "HarnessTargets"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "HarnessTargets": HarnessTargets,
    "IHarnessProtocol": IHarnessProtocol,
}
