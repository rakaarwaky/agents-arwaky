"""Capability — blender tool adapter (uv_venv install recipe).

Implements `IToolsProtocol` (AES403) and exports the `blender`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; shared mechanics live in
`utility_tool_mechanics`.
"""
from __future__ import annotations

from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
    dispatch_unit_op,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class BlenderToolsAdapter(IToolsProtocol):
    """Blender actions behind the tools protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        spec: ToolSpec | None = None,
        query: object | None = None,
        args: list[str] | None = None,
    ) -> object:
        """Dispatch *op* against this file's blender unit."""
        return dispatch_unit_op(self._units, op, spec, query, args, label="blender adapter")

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
    "blender": build_adapter_unit("blender", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "BlenderToolsAdapter",
]
