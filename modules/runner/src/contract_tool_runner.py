"""Tool-runner aggregate contract (AES102 `_aggregate`).

Implemented by the runner agent orchestrator, consumed by the surface layer.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_manifest_vo import Tool
from modules.shared.src.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)


class IToolExecutor(ABC):
    """Capability contract for locating and executing installed tools."""

    @abstractmethod
    def find_executable(self, spec: ToolSpec) -> Path | None:
        """Return the path of the runnable binary, or None when not runnable."""
        raise NotImplementedError

    @abstractmethod
    def run(self, spec: ToolSpec, args: list[str]) -> int:
        """Execute the tool binary with *args*; return a process exit code."""
        raise NotImplementedError


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
