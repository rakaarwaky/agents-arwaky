"""Harness-domain aggregate contract (agent orchestrator ABC).

The single agent resolves raw CLI tokens to canonical harness ids
(``resolve_targets`` / ``all_targets``) and routes each action
(connect / disconnect / provision_skills) to its capability.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_harness_vo import (
    ExitCode,
    HarnessConfig,
    HarnessTargets,
)


class IHarnessAggregate(ABC):
    """Aggregate resolving targets and routing actions to capabilities."""

    @abstractmethod
    def resolve_targets(self, targets: HarnessTargets) -> HarnessTargets:
        """Map raw CLI tokens (id / alias / --all) onto canonical ids, deduped."""
        ...

    @abstractmethod
    def all_targets(self) -> HarnessTargets:
        """Every supported harness id (canonical)."""
        ...

    @abstractmethod
    def connect(self, targets: HarnessTargets, force: bool = False, dry_run: bool = False,
                mcp_only: bool = False, skills_only: bool = False, env_only: bool = False,
                router: bool = False, copy_skills: bool = False) -> ExitCode:
        """Connect the resolved harness targets; return exit code."""
        ...

    @abstractmethod
    def disconnect(self, targets: HarnessTargets, dry_run: bool = False) -> ExitCode:
        """Disconnect the resolved harness targets; return exit code."""
        ...

    @abstractmethod
    def provision_skills(self, targets: HarnessTargets, copy: bool = False, dry_run: bool = False) -> ExitCode:
        """Provision the skill pack into the resolved harness targets; return exit code."""
        ...

__all__ = ["ExitCode", "HarnessConfig", "HarnessTargets", "IHarnessAggregate"]

#
# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "HarnessConfig": HarnessConfig,
    "HarnessTargets": HarnessTargets,
    "IHarnessAggregate": IHarnessAggregate,
}
