"""Capability — mnemosyne tool adapter (uv_project recipe).

Implements `IToolsProtocol` (AES403) and exports the `mnemosyne`
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


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class MnemosyneToolsAdapter(IToolsProtocol):
    """Mnemosyne actions behind the tools protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Public Contract (domain protocol ONLY) ─────────────
    def execute(
        self,
        op: str,
        spec: ToolSpec | None = None,
        query: object | None = None,
        args: list[str] | None = None,
    ) -> object:
        """Dispatch *op* against this file's mnemosyne unit."""
        return dispatch_unit_op(self._units, op, spec, query, args, label="mnemosyne adapter")

    # ─── Block 3: Dunder Methods ─────────────────────────────────────
    def __repr__(self) -> str:
        return f"MnemosyneToolsAdapter(tools={len(self._units)})"


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
