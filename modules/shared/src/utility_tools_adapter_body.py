"""Shared adapter-unit dispatch for the tools feature (utility layer, stateless).

Each ``capabilities_tools_*_adapter.py`` implements ``IToolsAdapterProtocol``
by delegating to these functions, so the unit-lookup rules live in one place
without a shared base class. Nothing here stores state: the unit map and the
display label are passed in on every call.

The optional-``daemons`` tolerance in :func:`install_unit` matches unit
factories whose ``install`` does not accept the keyword.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, PinCheck, ToolPaths


def unit_for(units: dict[str, AdapterUnit], spec: ToolSpec, display: str) -> AdapterUnit:
    """Return the unit that owns *spec*; raise when no unit claims its id."""
    unit = units.get(spec.id)
    if unit is None:
        raise ToolUpdateError(f"{display} adapter has no unit for {spec.id!r}")
    return unit


def satisfied_unit(
    units: dict[str, AdapterUnit],
    spec: ToolSpec,
    display: str,
    root: Path | None = None,
) -> bool:
    """True when *spec*'s unit reports the tool as installed."""
    return unit_for(units, spec, display).satisfied(spec, root)


def is_pin_satisfied_unit(
    units: dict[str, AdapterUnit],
    spec: ToolSpec,
    display: str,
    root: Path | None = None,
) -> PinCheck:
    """Return ``(satisfied, reason)`` of *spec*'s unit against the manifest pin."""
    return unit_for(units, spec, display).is_pin_satisfied(spec, root or REPO_ROOT)


def owned_paths_unit(
    units: dict[str, AdapterUnit],
    spec: ToolSpec,
    display: str,
    root: Path | None = None,
) -> ToolPaths:
    """Return the paths the owning unit holds for *spec*."""
    return ToolPaths(unit_for(units, spec, display).owned_paths(spec, root or REPO_ROOT) or ())


def install_unit(
    units: dict[str, AdapterUnit],
    spec: ToolSpec,
    root: Path,
    display: str,
    *,
    daemons: object | None = None,
) -> ToolPaths:
    """Install or build *spec*; return the created paths."""
    unit = unit_for(units, spec, display)
    try:
        return ToolPaths(unit.install(spec, root, daemons=daemons) or ())
    except TypeError:
        return ToolPaths(unit.install(spec, root) or ())


def update_unit(
    units: dict[str, AdapterUnit],
    spec: ToolSpec,
    root: Path,
    display: str,
) -> ToolPaths:
    """Update *spec* to the manifest pin; return the rebuilt paths."""
    return ToolPaths(unit_for(units, spec, display).update(spec, root) or ())


def with_adapter_protocol(cls):
    """Attach the five ``IToolsAdapterProtocol`` methods to *cls*.

    Adapters keep their ``_units`` map and ``_display`` label; the protocol
    methods are identical one-line delegations everywhere, so they are
    attached here instead of being copied into every adapter file.
    """

    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when the installed binary satisfies the manifest."""
        return satisfied_unit(self._units, spec, self._display, root)

    def is_pin_satisfied(
        self, spec: ToolSpec, root: Path | None = None
    ) -> PinCheck:
        """Return ``(satisfied, reason)`` against the manifest pin."""
        return is_pin_satisfied_unit(self._units, spec, self._display, root)

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> ToolPaths:
        """Return the paths this adapter's install owns for *spec*."""
        return owned_paths_unit(self._units, spec, self._display, root)

    def install(
        self,
        spec: ToolSpec,
        root: Path,
        *,
        daemons: object | None = None,
    ) -> ToolPaths:
        """Install or build *spec* into *root*; return the created paths."""
        return install_unit(self._units, spec, root, self._display, daemons=daemons)

    def update(self, spec: ToolSpec, root: Path) -> ToolPaths:
        """Update *spec* to the manifest pin; return the rebuilt paths."""
        return update_unit(self._units, spec, root, self._display)

    cls.satisfied = satisfied
    cls.is_pin_satisfied = is_pin_satisfied
    cls.owned_paths = owned_paths
    cls.install = install
    cls.update = update
    # ABCMeta freezes __abstractmethods__ when the class is created, so the
    # names the decorator just filled in have to be released explicitly or
    # instantiation still fails on a missing implementation.
    cls.__abstractmethods__ = frozenset(cls.__abstractmethods__) - {
        "satisfied",
        "is_pin_satisfied",
        "owned_paths",
        "install",
        "update",
    }
    return cls


__all__ = [
    "install_unit",
    "is_pin_satisfied_unit",
    "owned_paths_unit",
    "satisfied_unit",
    "unit_for",
    "update_unit",
    "with_adapter_protocol",
]
