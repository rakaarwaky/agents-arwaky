"""Tool-domain capability contracts (AES102 `_protocol`).

One file for the tools feature. Each class below is one capability seam:
a class carries every method that capability implements, with one concrete
return type each, so a capability implements its class outright and never
carries stubs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import (
    InstallResult,
    ToolList,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.shared.src.taxonomy_tools_vo import (
    AdapterUnit,
    ExitCode,
    PinCheck,
    ToolArgs,
    ToolPaths,
    ToolQuery,
)
from modules.shared.src.utility_tool_mechanics import ROOT


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


class ToolsAdapterBody(IToolsAdapterProtocol):
    """Shared concrete body for every config-driven tool adapter.

    Each ``capabilities_tools_*_adapter.py`` subclasses this and supplies only
    its own ``ADAPTER_UNITS`` map and ``_display`` name. The six protocol
    methods are implemented once here so no adapter file carries a copy.
    """

    _display: str = "tools"

    def __init__(self, units: dict[str, AdapterUnit]) -> None:
        """Store the adapter's tool-id → unit map."""
        self._units = dict(units)

    def _unit_for(self, spec: ToolSpec) -> AdapterUnit:
        """Return the unit that owns *spec*; raises if none does."""
        unit = self._units.get(spec.id)
        if unit is None:
            raise ToolUpdateError(f"{self._display} adapter has no unit for {spec.id!r}")
        return unit

    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when *spec*'s unit reports installed state."""
        return self._unit_for(spec).satisfied(spec, root)

    def is_pin_satisfied(self, spec: ToolSpec, root: Path | None = None) -> PinCheck:
        """Return (satisfied, reason) against the manifest pin."""
        return self._unit_for(spec).is_pin_satisfied(spec, root or ROOT)

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> ToolPaths:
        """Return the paths this adapter owns for *spec*."""
        return ToolPaths(self._unit_for(spec).owned_paths(spec, root or ROOT) or ())

    def install(
        self,
        spec: ToolSpec,
        root: Path,
        *,
        daemons: object | None = None,
    ) -> ToolPaths:
        """Install or build *spec*; return the created paths."""
        unit = self._unit_for(spec)
        try:
            return ToolPaths(unit.install(spec, root, daemons=daemons) or ())
        except TypeError:
            return ToolPaths(unit.install(spec, root) or ())

    def update(self, spec: ToolSpec, root: Path) -> ToolPaths:
        """Update *spec* to the manifest pin; return the rebuilt paths."""
        return ToolPaths(self._unit_for(spec).update(spec, root) or ())

    def __repr__(self) -> ToolQuery:
        return f"{type(self).__name__}(tools={len(self._units)})"


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
    "ToolsAdapterBody",
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
    "ToolsAdapterBody": ToolsAdapterBody,
}
