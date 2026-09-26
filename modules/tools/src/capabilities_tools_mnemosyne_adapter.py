"""Capability — mnemosyne tool adapter (uv_project recipe).

Exports the `mnemosyne`
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
class MnemosyneToolsAdapter(ToolsAdapterBody):
    """mnemosyne actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'mnemosyne'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        super().__init__(dict(ADAPTER_UNITS) if units is None else units)

# ---------------------------------------------------------------------------
# Recipe (uv_project lifecycle)
# ---------------------------------------------------------------------------
CONFIG = ToolLifecycleConfig(
    lifecycle="uv_project",
    src_rel="vendor/mnemosyne",
    tool_name="mnemosyne",
    launchers=(("mnemosyne", "mnemosyne"), ("mnemosyne-mcp", "mnemosyne")),
    pin_reason="uv project (rebuild required)",
    satisfied_bin="mnemosyne",
    uv_args=("--extra", "mcp"),
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "mnemosyne": build_adapter_unit("mnemosyne", CONFIG),
}

__all__ = [
    "ADAPTER_UNITS",
    "MnemosyneToolsAdapter",
]
