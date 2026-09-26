"""Capability — google-workspace tool adapter (uv_project recipe).

Implements `IToolsAdapterProtocol` (AES403) and exports the `workspace`
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
class WorkspaceToolsAdapter(IToolsAdapterProtocol):
    """Google-workspace actions behind the tools adapter protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def _unit_for(self, spec: ToolSpec) -> AdapterUnit:
        """Look up the adapter unit that owns *spec*."""
        unit = self._units.get(spec.id)
        if unit is None:
            raise ToolUpdateError(f"workspace adapter has no unit for {spec.id!r}")
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
        return f"WorkspaceToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Recipe (uv_project lifecycle; google-workspace-mcp aliases workspace-mcp)
# ---------------------------------------------------------------------------
CONFIG = ToolLifecycleConfig(
    lifecycle="uv_project",
    src_rel="vendor/google-workspace-mcp",
    tool_name="google-workspace-mcp",
    launchers=(("workspace-mcp", "workspace-mcp"), ("google-workspace-mcp", "workspace-mcp")),
    pin_reason="uv project (rebuild required)",
    satisfied_bin="workspace-mcp",
    # google-workspace-mcp adalah alias PATH dari workspace-mcp.
    alias_second_to_first=True,
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "workspace": build_adapter_unit("workspace", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "WorkspaceToolsAdapter",
]
