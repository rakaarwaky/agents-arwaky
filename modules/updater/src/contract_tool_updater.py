"""Tool-updater capability contract (AES102 `_protocol`).

Implemented by capabilities, consumed by the agent orchestrator.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult


class IToolUpdater(ABC):
    """Capability contract for tool updates."""

    @abstractmethod
    def update(self, spec: ToolSpec) -> UpdateResult:
        """Update the tool described by *spec*; report outcome as UpdateResult."""
        raise NotImplementedError
