"""Capability — codegraph tool adapter (npm workspace recipe).

Exports the `codegraph`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the launcher writer is the
generic `build_adapter_unit` default (entry launcher + symlinks).
"""
from __future__ import annotations

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_tools_vo import (
    AdapterUnit,
    ToolLifecycleConfig,
)
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
)
from modules.shared.src.utility_tools_adapter_body import with_adapter_protocol


# ─── Block 1: Class Definition & Constructor ──────────────
@with_adapter_protocol
class CodegraphToolsAdapter(IToolsAdapterProtocol):
    """codegraph actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'codegraph'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        self._units = dict(ADAPTER_UNITS) if units is None else units



# ---------------------------------------------------------------------------
# Recipe (node lifecycle)
# ---------------------------------------------------------------------------
config = ToolLifecycleConfig(
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
    "codegraph": build_adapter_unit("codegraph", config),
}

__all__ = [
    "ADAPTER_UNITS",
    "CodegraphToolsAdapter",
]
