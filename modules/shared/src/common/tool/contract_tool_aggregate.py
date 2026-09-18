"""Tool-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.common.manifest.taxonomy_manifest_vo import Tool
from modules.shared.src.common.tool.taxonomy_tool_vo import (
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
        raise NotImplementedError

    @abstractmethod
    def install(self, spec: ToolSpec) -> InstallResult:
        """Install a single tool spec."""
        raise NotImplementedError

    @abstractmethod
    def update(self, spec: ToolSpec) -> UpdateResult:
        """Update a single tool spec (git pull + reinstall)."""
        raise NotImplementedError

    @abstractmethod
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Uninstall a single tool spec."""
        raise NotImplementedError

    @abstractmethod
    def run_tool(self, spec: ToolSpec, args: list[str]) -> int:
        """Run the tool binary; returns the process exit code."""
        raise NotImplementedError

    @abstractmethod
    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Resolve the runnable binary path for a spec, or None."""
        raise NotImplementedError
