"""Capability — ponytail tool adapter (npm workspace recipe).

Exports the `ponytail`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the launcher writer is the
generic `build_adapter_unit` default and only the npm-ci post-copy
hook is defined here.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_tools_protocol import ToolsAdapterBody
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
    run,
)

# ─── Block 1: Class Definition & Constructor ──────────────
class PonytailToolsAdapter(ToolsAdapterBody):
    """ponytail actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'ponytail'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        super().__init__(dict(ADAPTER_UNITS) if units is None else units)

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
