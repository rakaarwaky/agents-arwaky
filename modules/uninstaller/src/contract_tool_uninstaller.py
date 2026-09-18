"""Tool-uninstaller capability contract (AES102 `_protocol`).

Implemented by capabilities, consumed by the agent orchestrator.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult


class IToolUninstaller(ABC):
    """Capability contract for tool uninstallation."""

    @abstractmethod
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Uninstall the tool described by *spec*; report outcome."""
        raise NotImplementedError
