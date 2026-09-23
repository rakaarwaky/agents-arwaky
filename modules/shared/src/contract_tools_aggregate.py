"""Tool-domain aggregate contract (AES102 `_aggregate`).

`IToolsAggregate` is the zero-I/O composition of the four lifecycle actions
(install, update, uninstall, run) plus manifest target resolution. It is
the single entry point the CLI surface calls; `ToolsOrchestrator`
implements it and delegates every side effect to a capability.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_common_vo import (
    InstallResult,
    Tool,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.shared.src.taxonomy_tools_vo import ExitCode, ToolQuery


class IToolsAggregate(ABC):
    """Zero-I/O aggregate over all tool-lifecycle capabilities."""

    @abstractmethod
    def list_tools(self) -> list[Tool]:
        """Return every registered tool from the manifest."""
        return None

    @abstractmethod
    def resolve_spec(self, query: ToolQuery) -> ToolSpec | None:
        """Resolve a manifest id / binary / alias into a ToolSpec; None when unknown."""
        return None

    @abstractmethod
    def install(self, spec: ToolSpec) -> InstallResult:
        """Install a single tool spec (provision + launcher registration)."""
        return None

    @abstractmethod
    def update(self, spec: ToolSpec) -> UpdateResult:
        """Update a single tool spec (bump + record transition)."""
        return None

    @abstractmethod
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Uninstall a single tool spec (remove + verify)."""
        return None

    @abstractmethod
    def run_tool(self, spec: ToolSpec, args: list[str]) -> ExitCode:
        """Run the tool; returns the process exit code."""
        return None

    @abstractmethod
    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Discover the launch path (read-only) for the CLI surface."""
        return None


__all__ = [
    "IToolsAggregate",
    "InstallResult",
    "UninstallResult",
    "UpdateResult",
]
