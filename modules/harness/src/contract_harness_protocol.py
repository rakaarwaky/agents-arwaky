"""Harness-domain protocol contract (capability ABC)."""
from __future__ import annotations
from modules.harness.src.taxonomy_harness_vo import HarnessConfig


from abc import ABC, abstractmethod


class IHarnessConnector(ABC):
    """Capability contract for one agent harness connect/disconnect."""

    @abstractmethod
    def connect(
        self,
        force: bool,
        dry_run: bool,
        mcp_only: bool,
        skills_only: bool,
        env_only: bool,
        copy_skills: bool = False,
    ) -> None:
        """Connect this harness: merge MCP, provision skills, inject env."""
        return None

    @abstractmethod
    def disconnect(self, force: bool, dry_run: bool) -> None:
        """Disconnect this harness: remove MCP servers, skills and env keys."""
        return None

__all__ = ['HarnessConfig']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"HarnessConfig": HarnessConfig}
