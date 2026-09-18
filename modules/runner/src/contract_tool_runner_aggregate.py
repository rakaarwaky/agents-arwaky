"""Tool-runner aggregate contract (AES102 `_aggregate`).

Implemented by the runner agent orchestrator, consumed by the surface layer.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_manifest_vo import Tool
from modules.shared.src.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)


class IToolAggregate(ABC):
    """Aggregate over all tool-management capabilities."""

    @abstractmethod
    def list_tools(self) -> list[Tool]:
        """Return every registered tool from the manifest."""
        return None

    @abstractmethod
    def install(self, spec: ToolSpec) -> InstallResult:
        """Install a single tool spec."""
        return None

    @abstractmethod
    def update(self, spec: ToolSpec) -> UpdateResult:
        """Update a single tool spec (git pull + reinstall)."""
        return None

    @abstractmethod
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Uninstall a single tool spec."""
        return None

    @abstractmethod
    def run_tool(self, spec: ToolSpec, args: list[str]) -> int:
        """Run the tool binary; returns the process exit code."""
        return None
