"""Tool-domain capability contracts (AES102 `_protocol`).

One file for the tools feature. Each class below is one capability seam:
a class carries every method that capability implements, with one concrete
return type each, so a capability implements its class outright and never
carries stubs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_common_vo import (
    InstallResult,
    ToolList,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.shared.src.taxonomy_tools_vo import ExitCode, PinCheck, ToolArgs, ToolPaths, ToolQuery


class IToolsInstallerProtocol(ABC):
    """Install action: provision + register launcher."""

    @abstractmethod
    def install(
        self,
        spec: ToolSpec,
        adapter: object | None = None,
        dry_run: bool = False,
    ) -> InstallResult:
        """Provision *spec* via its adapter, register launchers."""
        ...


class IToolsUpdaterProtocol(ABC):
    """Update action: bump to manifest pin + record transition."""

    @abstractmethod
    def update(
        self,
        spec: ToolSpec,
        adapter: object | None = None,
        dry_run: bool = False,
    ) -> UpdateResult:
        """Bump *spec* to its pin and record the transition."""
        ...


class IToolsUninstallerProtocol(ABC):
    """Uninstall action: remove owned paths + verify residuals."""

    @abstractmethod
    def uninstall(
        self,
        spec: ToolSpec,
        owned_paths: ToolPaths | None = None,
    ) -> UninstallResult:
        """Remove *spec*'s owned paths and report residuals."""
        ...


class IToolsRunnerProtocol(ABC):
    """Run action: discover executable then exec it."""

    @abstractmethod
    def run(self, spec: ToolSpec, args: ToolArgs) -> ExitCode:
        """Execute the discovered binary with *args*; return the exit code."""
        ...

    @abstractmethod
    def discover(self, spec: ToolSpec) -> Path | None:
        """Discover the launch path for *spec*; None when absent."""
        ...


class IToolsAdapterProtocol(ABC):
    """Adapter seam: probes and lifecycle hooks exposed per tool unit."""

    @abstractmethod
    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when the installed binary satisfies the manifest."""
        ...

    @abstractmethod
    def is_pin_satisfied(self, spec: ToolSpec, root: Path | None = None) -> PinCheck:
        """(satisfied, reason) against the manifest pin."""
        ...

    @abstractmethod
    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> ToolPaths:
        """Paths owned by this adapter's install."""
        ...

    @abstractmethod
    def install(self, spec: ToolSpec, root: Path, *, daemons: object | None = None) -> ToolPaths:
        """Install/build into *root*; returns created paths."""
        ...

    @abstractmethod
    def update(self, spec: ToolSpec, root: Path) -> ToolPaths:
        """Update to the manifest pin; returns rebuilt paths."""
        ...


__all__ = [
    "ExitCode",
    "IToolsAdapterProtocol",
    "IToolsInstallerProtocol",
    "IToolsRunnerProtocol",
    "IToolsUninstallerProtocol",
    "IToolsUpdaterProtocol",
    "PinCheck",
    "ToolArgs",
    "ToolList",
    "ToolPaths",
    "ToolQuery",
    "ToolSpec",
]

_layer_symbols = {
    "ExitCode": ExitCode,
    "IToolsAdapterProtocol": IToolsAdapterProtocol,
    "IToolsInstallerProtocol": IToolsInstallerProtocol,
    "IToolsRunnerProtocol": IToolsRunnerProtocol,
    "IToolsUninstallerProtocol": IToolsUninstallerProtocol,
    "IToolsUpdaterProtocol": IToolsUpdaterProtocol,
    "PinCheck": PinCheck,
    "ToolArgs": ToolArgs,
    "ToolList": ToolList,
    "ToolPaths": ToolPaths,
    "ToolQuery": ToolQuery,
    "ToolSpec": ToolSpec,
}
