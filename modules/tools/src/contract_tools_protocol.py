"""Tool-domain capability + adapter contracts (AES102 `_protocol`).

Implemented by the four verb capability classes and the unified
per-tool leaf adapters; consumed by the `ToolsOrchestrator` agent.

The adapter ABC is deliberately per-tool but multi-verb: a single
`utility_<tool>_adapter.py` class knows that tool's install, update,
pin-comparison, and owned-teardown data in one place.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)


class IToolAdapter(ABC):
    """Unified leaf adapter: knows exactly one manifest tool's lifecycle.

    Adapters import only `modules.shared.src.*`,
    `modules.tools.src.utility_adapter_base`, and stdlib (no
    capability/agent/root/contract imports, no utility-to-utility
    imports). Daemon service-install delegation uses importlib with
    string-concatenated module names so the purity grep stays clean.
    """

    #: Tool ids whose lifecycle includes a systemd unit or Podman container.
    is_daemon: bool = False

    # -- install (FR-001) ---------------------------------------------------------
    def install(self, spec: ToolSpec, root: Path, *, daemons=None) -> list[Path]:
        """Run this tool's package-manager/build sequence; return artifact paths.

        Raises on failure — the provisioner catches it and folds the captured
        diagnostic into the InstallResult. Daemon-backed adapters receive the
        injected daemon aggregate via *daemons*.
        """
        return []

    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when the tool is already installed at its pin (skip the adapter)."""
        return False

    # -- update (FR-003) ----------------------------------------------------------
    @abstractmethod
    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        """Run this tool's update/rebuild sequence; return paths touched."""
        return []

    @abstractmethod
    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        """Return (satisfied, description) after comparing installed state to the
        manifest pin. The adapter decides what "installed" means for its tool."""
        return (False, "")

    # -- uninstall data (FR-005) ----------------------------------------------------
    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """DATA only: launcher/alias names + XDG data/cache dirs + extra owned
        paths the installer created for this tool. The remover capability
        consumes this; the adapter is the single source of per-tool teardown
        data."""
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

        Runs only after FR-001 success; foreign no-provenance launchers are
        reported as residual, never overwritten.
        """
        return None


class IToolBumper(ABC):
    """FR-003: bring a tool to its manifest pin; never raises out."""

    @abstractmethod
    def bump(self, spec: ToolSpec, adapter: IToolAdapter, dry_run: bool = False) -> UpdateResult:
        """Pin comparison → adapter dispatch → capture diagnostics into the result.

        Every failure path returns UpdateResult(success=False, message).
        """
        return None


class IToolRecorder(ABC):
    """FR-004: record the version transition after a successful bump."""

    @abstractmethod
    def record(self, spec: ToolSpec, update_result: UpdateResult) -> UpdateResult:
        """Log the transition; idempotent no-op when nothing moved.

        Runs only after FR-003 success; a failed bump yields no record.
        """
        return None


class IToolRemover(ABC):
    """FR-005: delete a tool's owned state; never raises out of ``remove``."""

    @abstractmethod
    def remove(self, spec: ToolSpec, owned_paths: list[Path], dry_run: bool = False) -> UninstallResult:
        """Stop the daemon (if applicable) then remove launchers + XDG data/cache.

        Scoped strictly to the owned set. Every failure path returns
        UninstallResult(success=False, message).
        """
        return None


class IToolVerifier(ABC):
    """FR-006: confirm the owned set is gone; report residuals by name."""

    @abstractmethod
    def verify(self, spec: ToolSpec, uninstall_result: UninstallResult) -> UninstallResult:
        """Runs after FR-005 (success or partial); a failed removal still gets
        verified so residuals are surfaced, not hidden. Nothing raises into
        the CLI surface — verification failures append to the UninstallResult."""
        return None


class IToolDiscoverer(ABC):
    """FR-007: resolve the concrete launch path for a ToolSpec.

    Universal discovery order (identical for every tool): XDG bin launcher
    -> host PATH -> per-tool install dir. Read-only: never mutates install
    state, never invokes a package manager. No candidate found -> None.
    """

    @abstractmethod
    def discover(self, spec: ToolSpec, root: Path | None = None) -> Path | None:
        """Return the executable path to launch, resolved; None when absent."""
        return None


class IToolExecutor(ABC):
    """FR-008: launch a discovered executable and return its exit code.

    Every failure path returns an int; nothing raises out of `execute`
    into the CLI surface. A distinct non-zero sentinel is reserved for
    "executable vanished between discovery and launch".
    """

    @abstractmethod
    def execute(self, spec: ToolSpec, executable: Path, args: list[str], root: Path | None = None) -> int:
        """Run the resolved *executable* with *args*; return the child's exit code."""
        return None


__all__ = [
    "IToolAdapter",
    "IToolBumper",
    "IToolDiscoverer",
    "IToolExecutor",
    "IToolLauncherRegistrar",
    "IToolProvisioner",
    "IToolRecorder",
    "IToolRemover",
    "IToolVerifier",
]
