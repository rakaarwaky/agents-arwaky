"""Harness-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations
from modules.harness.src.taxonomy_harness_vo import HarnessConfig


from abc import ABC, abstractmethod


class IHarnessAggregate(ABC):
    """Aggregate routing connect/disconnect to per-harness connectors."""

    @abstractmethod
    def connect(
        self,
        targets: tuple[str, ...],
        force: bool = False,
        dry_run: bool = False,
        mcp_only: bool = False,
        skills_only: bool = False,
        env_only: bool = False,
        copy_skills: bool = False,
    ) -> int:
        """Connect the resolved harness targets; return exit code."""
        return None

    @abstractmethod
    def disconnect(self, targets: tuple[str, ...], dry_run: bool = False) -> int:
        """Disconnect the resolved harness targets; return exit code."""
        return None

__all__ = ['HarnessConfig']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"HarnessConfig": HarnessConfig}
