"""Capability — google-workspace tool adapter (uv_project recipe).

Exports the `workspace`
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
class WorkspaceToolsAdapter(ToolsAdapterBody):
    """workspace actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'workspace'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        super().__init__(dict(ADAPTER_UNITS) if units is None else units)

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
