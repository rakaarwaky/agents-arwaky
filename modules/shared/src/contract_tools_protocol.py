"""Tool-domain capability contracts (AES102 `_protocol`).

Five ABCs in one module: four action ABCs (installer / updater /
uninstaller / runner), one action per business-action, plus
`IToolAdapterFacade` — the single API surface the action capabilities
call to reach a tool's per-adapter action functions.

`IToolAdapterFacade` deliberately replaces the previous "registry of
adapter modules + each capability resolves its own adapter + inlined
shared helpers" scattering with one injected facade so:

- the per-tool adapter units and shared mechanics all live in one
  capability file, `capabilities_tools_adapter.py` (registered god
  object, AES301 exception) with no `utility_*` adapter modules —
  reached only through this facade;
- a new tool is one manifest entry + one adapter unit in that file;
  nothing else changes.

The facade protocol is implemented by `capabilities_tools_adapter`
(`ToolAdapterFacade`), wired by the root container and injected into
the four action capabilities (dependency inversion: capabilities depend
on this protocol, not on the concrete facade).

The adapter parameter on ``IToolInstaller.install`` /
``IToolUpdater.update`` is typed ``object`` — a concrete leaf adapter
instance. The protocol layer stays free of any utility-layer import,
so no forward reference or TYPE_CHECKING import is needed.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_common_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)


class IToolInstaller(ABC):
    """FR-001: install a tool to its manifest pin, register its launcher."""

    @abstractmethod
    def install(
        self,
        spec: ToolSpec,
        adapter: object,
        dry_run: bool = False,
    ) -> InstallResult:
        """Provision → register launcher → health probe, one action.

        *adapter* is a concrete leaf adapter instance
        (e.g. the `vision` or `workspace` adapter modules).

        Sub-steps (internal, not separate protocol methods):
        1. Satisfied check gates the idempotent skip; otherwise dispatch
           the adapter's `install` sequence.
        2. Register one launcher per binary plus one per manifest alias
           under XDG bin. Foreign no-provenance launchers are reported as
           residual, never overwritten.
        3. Post-install health probe (`<binary> --version` agreement).

        Every failure path returns InstallResult(success=False, message);
        nothing raises out.
        """
        return None


class IToolUpdater(ABC):
    """FR-002: bring a tool to its manifest pin, record the transition."""

    @abstractmethod
    def update(
        self,
        spec: ToolSpec,
        adapter: object,
        dry_run: bool = False,
    ) -> UpdateResult:
        """Pin check → adapter update → record transition, one action.

        *adapter* is a concrete leaf adapter instance
        (e.g. the `vision` or `workspace` adapter modules).

        Sub-steps (internal, not separate protocol methods):
        1. Pin comparison first (idempotence); on unsatisfied state
           dispatch the adapter's `update` sequence.
        2. After a successful bump, write a version-transition record
           under the tool's XDG state dir. Idempotent: re-recording the
           same transition is a no-op.

        Every failure path returns UpdateResult(success=False, message);
        nothing raises out. A failed bump yields no record.
        """
        return None


class IToolUninstaller(ABC):
    """FR-003: remove a tool's owned state, verify residuals."""

    @abstractmethod
    def uninstall(
        self,
        spec: ToolSpec,
        owned_paths: list[Path],
        dry_run: bool = False,
    ) -> UninstallResult:
        """Stop daemon → remove owned paths → verify residuals, one action.

        Sub-steps (internal, not separate protocol methods):
        1. Stop the daemon (if applicable) first; an active unit that
           refuses to stop becomes a named residual, never force-killed.
        2. Remove launchers + XDG data/cache/config, scoped strictly to
           the owned set.
        3. Verify: launchers gone from XDG bin, binary absent from PATH,
           data/cache subtrees removed, daemon unit absent. Anything
           surviving becomes a named residual.

        A failed removal still gets verified so residuals are surfaced,
        not hidden. Nothing raises into the CLI surface.
        """
        return None


class IToolRunner(ABC):
    """FR-004: discover a tool's executable and run it, returning exit code."""

    @abstractmethod
    def run(
        self,
        spec: ToolSpec,
        args: list[str],
        root: Path | None = None,
    ) -> int:
        """Discover → execute → return the child's real exit code, one action.

        Sub-steps (internal, not separate protocol methods):
        1. Discover in a universal deterministic order: XDG bin launcher
           → host PATH → per-tool install dir. MCP tools resolve through
           `mcp_binary` first. Read-only: never mutates install state.
           No candidate → return 1.
        2. Plain subprocess exec of the discovered path with forwarded
           args. Daemons are invoked through their launcher, never
           spawned ad hoc. Sentinel 126 is reserved for "executable
           vanished between discovery and launch".

        Every failure path returns an int; nothing raises out.
        """
        return 0


class IToolAdapterFacade(ABC):
    """Standardized single-API pipeline over all per-tool adapters.

    One action per business action, each returning the value the calling
    capability needs. `satisfied` / `owned_paths` are read-only;
    `install` / `update` mutate (or dry-run) XDG state.

    Nothing here raises for an unknown tool id: `resolve` returns `None`
    and the action methods are only called after a successful resolve.
    """

    @abstractmethod
    def resolve(self, spec: ToolSpec) -> object:
        """Return the per-tool adapter unit for *spec*, or None when unregistered.

        For shared-module ids (`anytype-daemon`) the unit is a namespace
        over the module's `daemon_*` leaf functions, so the action surface
        is uniform across every registered tool.
        """
        return None

    @abstractmethod
    def is_registered(self, spec: ToolSpec) -> bool:
        """True when *spec.id* has an adapter unit in the registry."""
        return False

    @abstractmethod
    def satisfied(self, spec: ToolSpec) -> bool:
        """Adapter's idempotence probe (True when the tool is already at pin)."""
        return False

    @abstractmethod
    def is_pin_satisfied(self, spec: ToolSpec) -> tuple[bool, str]:
        """Adapter's pin-check for the updater (True, reason) when satisfied."""
        return (False, "unknown")

    @abstractmethod
    def install(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Run the adapter's install sequence; return created/updated paths."""
        return []

    @abstractmethod
    def update(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Run the adapter's update sequence; return created/updated paths."""
        return []

    @abstractmethod
    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """The adapter's owned XDG set (launchers + data + config + extras)."""
        return []


__all__ = [
    "IToolAdapterFacade",
    "IToolInstaller",
    "IToolRunner",
    "IToolUninstaller",
    "IToolUpdater",
]
