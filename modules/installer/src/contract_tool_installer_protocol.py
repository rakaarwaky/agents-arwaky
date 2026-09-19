"""Tool-installer capability/adapter contracts (AES102 `_protocol`).

Implemented by the two business-action capabilities and the per-tool leaf
adapters; consumed by the agent orchestrator.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec


class IToolAdapter(ABC):
    """Leaf adapter: knows exactly one manifest tool's install/build sequence.

    Adapters import only `modules/shared/...` and stdlib (no capability/agent/
    root/contract imports, no utility-to-utility imports).
    """

    def install(self, spec: ToolSpec, root: Path, *, daemons=None) -> list[Path]:
        """Run this tool's package-manager/build sequence; return artifact paths.

        Raises on failure — the provisioner catches it and folds the captured
        diagnostic into the InstallResult. Daemon-backed adapters receive the
        injected daemon aggregate via *daemons*.
        """
        return []


class IToolProvisioner(ABC):
    """FR-001: ensure the tool exists at its manifest pin; never raises out."""

    @abstractmethod
    def provision(self, spec: ToolSpec, adapter: IToolAdapter, dry_run: bool = False) -> InstallResult:
        """Satisfied check → adapter dispatch → health probe.

        Every failure path returns InstallResult(success=False, message).
        """
        return None


class IToolLauncherRegistrar(ABC):
    """FR-002: register a provisioned tool's launcher(s) under XDG bin."""

    @abstractmethod
    def register_launcher(self, spec: ToolSpec, install_result: InstallResult) -> InstallResult:
        """Register one launcher per binary plus one per manifest alias.

        Runs only after FR-001 success; write/chmod mechanics stay in
        utility_launcher_writer. Foreign no-provenance launchers are reported
        as residual, never overwritten.
        """
        return None


class IToolInstaller(ABC):
    """Single install verb over the two capabilities (orchestrator surface)."""

    @abstractmethod
    def install(self, spec: ToolSpec) -> InstallResult:
        """Provision then register; returns the (possibly folded) InstallResult."""
        return None


__all__ = [
    "IToolAdapter",
    "IToolInstaller",
    "IToolLauncherRegistrar",
    "IToolProvisioner",
]
