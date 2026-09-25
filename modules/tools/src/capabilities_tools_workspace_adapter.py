"""Capability — google-workspace tool adapter (uv_project recipe).

Implements `IToolsProtocol` (AES403) and exports the `workspace`
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
class WorkspaceToolsAdapter(IToolsProtocol):
    """Google-workspace actions behind the tools protocol (AES403 implementor)."""

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
        """Dispatch *op* against this file's workspace unit."""
        return dispatch_unit_op(self._units, op, spec, query, args, label="workspace adapter")

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
