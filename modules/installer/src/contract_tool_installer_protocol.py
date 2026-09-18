"""Tool-installer capability contract (AES102 `_protocol`).

Implemented by capabilities, consumed by the agent orchestrator.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec


class IToolInstaller(ABC):
    """Capability contract for tool installation."""

    @abstractmethod
    def install(self, spec: ToolSpec) -> InstallResult:
        """Install the tool described by *spec*; report outcome as InstallResult."""
        return None
