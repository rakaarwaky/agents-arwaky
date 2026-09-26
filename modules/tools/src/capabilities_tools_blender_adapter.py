"""Capability — blender tool adapter (uv_venv install recipe).

Implements `IToolsAdapterProtocol` (AES403) and exports the `blender`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; shared mechanics live in
`utility_tool_mechanics`.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    ROOT,
    build_adapter_unit,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class BlenderToolsAdapter(IToolsAdapterProtocol):
    """Blender actions behind the tools adapter protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def _unit_for(self, spec: ToolSpec) -> AdapterUnit:
        """Look up the adapter unit that owns *spec*."""
        unit = self._units.get(spec.id)
        if unit is None:
            raise ToolUpdateError(f"blender adapter has no unit for {spec.id!r}")
        return unit

    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when *spec*'s unit reports installed state."""
        return self._unit_for(spec).satisfied(spec, root)

    def is_pin_satisfied(self, spec: ToolSpec, root: Path | None = None) -> tuple[bool, str]:
        """Return (satisfied, reason) against the manifest pin."""
        return self._unit_for(spec).is_pin_satisfied(spec, root or ROOT)

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Return the paths this adapter owns for *spec*."""
        return list(self._unit_for(spec).owned_paths(spec, root or ROOT) or [])

    def install(self, spec: ToolSpec, root: Path, *, daemons: object | None = None) -> list[Path]:
        """Install or build *spec*; return the created paths."""
        unit = self._unit_for(spec)
        try:
            return list(unit.install(spec, root, daemons=daemons) or [])
        except TypeError:
            return list(unit.install(spec, root) or [])

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        """Update *spec* to the manifest pin; return the rebuilt paths."""
        return list(self._unit_for(spec).update(spec, root) or [])

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return f"BlenderToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Recipe (uv_venv lifecycle)
# ---------------------------------------------------------------------------
CONFIG = ToolLifecycleConfig(
    lifecycle="uv_venv",
    src_rel="internal/blender-arwaky",
    tool_name="blender-arwaky",
    launchers=(
        ("blender-arwaky", "blender-arwaky"),
        ("ba", "blender-arwaky"),
        ("blender-mcp", "blender-mcp"),
    ),
    pin_reason="venv/pip (rebuild required)",
    satisfied_bin="blender-arwaky",
    init_message="Run 'blender-arwaky init' to setup workspace symlinks",
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "blender-arwaky": build_adapter_unit("blender-arwaky", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "BlenderToolsAdapter",
]
