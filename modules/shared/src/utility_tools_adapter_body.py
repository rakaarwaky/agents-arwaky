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



__all__ = [
    "install_unit",
    "is_pin_satisfied_unit",
    "owned_paths_unit",
    "satisfied_unit",
    "unit_for",
    "update_unit",
]
