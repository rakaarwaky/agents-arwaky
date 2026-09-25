"""Capability — codegraph tool adapter (npm workspace recipe).

Implements `IToolsProtocol` (AES403) and exports the `codegraph`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the launcher writer is the
generic `build_adapter_unit` default (entry launcher + symlinks).
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
class CodegraphToolsAdapter(IToolsProtocol):
    """Codegraph actions behind the tools protocol (AES403 implementor)."""

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
        """Dispatch *op* against this file's codegraph unit."""
        return dispatch_unit_op(self._units, op, spec, query, args, label="codegraph adapter")

    # ─── Block 3: Dunder Methods ─────────────────────────────────────
    def __repr__(self) -> str:
        return f"CodegraphToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Recipe (node lifecycle)
# ---------------------------------------------------------------------------
CONFIG = ToolLifecycleConfig(
    lifecycle="node",
    src_rel="vendor/codegraph",
    app_name="codegraph",
    entry="dist/bin/codegraph.js",
    launchers=("codegraph-mcp", "codegraph"),
    pin_reason="npm workspace (rebuild required)",
    satisfied_bin="codegraph-mcp",
    requires=("npm", "codegraph requires npm (https://nodejs.org)"),
    install_cmd=("npm", "ci", "--no-audit", "--no-fund"),
    build_cmd=("npm", "run", "build"),
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "codegraph": build_adapter_unit("codegraph", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "CodegraphToolsAdapter",
]
