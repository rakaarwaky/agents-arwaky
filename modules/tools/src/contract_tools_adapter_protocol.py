"""Contract — unified per-tool adapter facade protocol (AES102 `_protocol`).

`IToolAdapterFacade` is the single API surface the four lifecycle
capabilities (installer / updater / uninstaller / runner) call to reach
a tool's per-adapter verb functions and the shared adapter mechanics.
It deliberately replaces the previous "registry of adapter modules +
each capability resolves its own adapter + inlined shared helpers"
scattering with one injected facade so:

- the per-tool adapter units and shared mechanics all live in one
  capability file, `capabilities_tools_adapter.py` (registered god
  object, AES301 exception) with no `utility_*` adapter modules —
  reached only through this facade;
- a new tool is one manifest entry + one adapter unit in that file;
  nothing else changes.

The protocol is implemented by `capabilities_tools_adapter`
(`ToolAdapterFacade`), wired by the root container and injected into
the four verb capabilities (dependency inversion: capabilities depend
on this protocol, not on the concrete facade).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec


class IToolAdapterFacade(ABC):
    """Standardized single-API pipeline over all per-tool adapters.

    One verb per business action, each returning the value the calling
    capability needs. `satisfied` / `owned_paths` are read-only;
    `install` / `update` mutate (or dry-run) XDG state.

    Nothing here raises for an unknown tool id: `resolve` returns `None`
    and the verb methods are only called after a successful resolve.
    """

    @abstractmethod
    def resolve(self, spec: ToolSpec) -> object:
        """Return the per-tool adapter unit for *spec*, or None when unregistered.

        For shared-module ids (`anytype-daemon`) the unit is a namespace
        over the module's `daemon_*` leaf functions, so the verb surface
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


__all__ = ["IToolAdapterFacade"]
