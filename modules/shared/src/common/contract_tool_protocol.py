"""Tool-domain protocol contracts (capability ABCs)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.tool.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)


class IToolInstaller(ABC):
    """Capability contract for tool installation."""

    @abstractmethod
    def install(self, spec: ToolSpec) -> InstallResult:
        """Install the tool described by *spec*; report outcome as InstallResult."""
        raise NotImplementedError


class IToolUpdater(ABC):
    """Capability contract for tool updates."""

    @abstractmethod
    def update(self, spec: ToolSpec) -> UpdateResult:
        """Update the tool described by *spec*; report outcome as UpdateResult."""
        raise NotImplementedError


class IToolUninstaller(ABC):
    """Capability contract for tool uninstallation."""

    @abstractmethod
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Uninstall the tool described by *spec*; report outcome."""
        raise NotImplementedError


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
