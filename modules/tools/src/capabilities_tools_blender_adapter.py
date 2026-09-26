"""Capability — blender tool adapter (uv_venv install recipe).

Exports the `blender`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; shared mechanics live in
`utility_tool_mechanics`.
"""
from __future__ import annotations

from modules.shared.src.contract_tools_protocol import ToolsAdapterBody
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
)

# ─── Block 1: Class Definition & Constructor ──────────────
class BlenderToolsAdapter(ToolsAdapterBody):
    """blender actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'blender'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        super().__init__(dict(ADAPTER_UNITS) if units is None else units)

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
