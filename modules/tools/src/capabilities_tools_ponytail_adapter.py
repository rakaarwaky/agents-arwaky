"""Capability — ponytail tool adapter (npm workspace recipe).

Implements `IToolsProtocol` (AES403) and exports the `ponytail`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the launcher writer is the
generic `build_adapter_unit` default and only the npm-ci post-copy
hook is defined here.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
    dispatch_unit_op,
    run,
)


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class PonytailToolsAdapter(IToolsProtocol):
    """Ponytail actions behind the tools protocol (AES403 implementor)."""

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
        """Dispatch *op* against this file's ponytail unit."""
        return dispatch_unit_op(self._units, op, spec, query, args, label="ponytail adapter")

    # ─── Block 3: Dunder Methods ─────────────────────────────────────
    def __repr__(self) -> str:
        return f"PonytailToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Recipe (node lifecycle + npm ci post-copy hook)
# ---------------------------------------------------------------------------
def _ponytail_post_copy(app_dir: Path) -> None:
    mcp_dir = app_dir / "ponytail-mcp"
    if (mcp_dir / "package.json").exists():
        run(["npm", "ci", "--no-audit", "--no-fund"], mcp_dir)


CONFIG = ToolLifecycleConfig(
    lifecycle="node",
    src_rel="vendor/ponytail",
    app_name="ponytail",
    launchers=("ponytail-mcp",),
    entry="ponytail-mcp/index.js",
    ignores=("node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv"),
    pin_reason="npm workspace (rebuild required)",
    satisfied_bin="ponytail-mcp",
    requires=("npm", "ponytail requires npm (https://nodejs.org)"),
    node_post_copy_hook=_ponytail_post_copy,
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "ponytail": build_adapter_unit("ponytail", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "PonytailToolsAdapter",
]
