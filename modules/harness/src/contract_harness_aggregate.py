"""Harness-domain aggregate contract (agent orchestrator ABC).

The single agent routes each verb (connect / disconnect / provision_skills)
to its capability after resolving raw CLI tokens to canonical harness ids.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.harness.src.taxonomy_harness_vo import ExitCode, HarnessConfig


class IHarnessAggregate(ABC):
    """Aggregate routing connect / disconnect / provision_skills to capabilities."""

    @abstractmethod
    def resolve_targets(self, targets: tuple[str, ...]) -> tuple[str, ...]:
        """Map raw CLI tokens (id / alias / --all) onto canonical ids, deduped."""
        return None

    @abstractmethod
    def connect(self, targets: tuple[str, ...], force: bool = False, dry_run: bool = False,
                mcp_only: bool = False, skills_only: bool = False, env_only: bool = False,
                router: bool = False, copy_skills: bool = False) -> ExitCode:
        """Connect the resolved harness targets; return exit code."""
        return None

    @abstractmethod
    def disconnect(self, targets: tuple[str, ...], dry_run: bool = False) -> ExitCode:
        """Disconnect the resolved harness targets; return exit code."""
        return None

    @abstractmethod
    def provision_skills(self, targets: tuple[str, ...], copy: bool = False, dry_run: bool = False) -> ExitCode:
        """Provision the skill pack into the resolved harness targets; return exit code."""
        return None


__all__ = ["ExitCode", "HarnessConfig", "IHarnessAggregate"]

#
# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "HarnessConfig": HarnessConfig,
    "IHarnessAggregate": IHarnessAggregate,
}
