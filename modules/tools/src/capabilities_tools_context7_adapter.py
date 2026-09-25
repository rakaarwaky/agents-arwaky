"""Capability — context7 tool adapter (pnpm workspace recipe).

Implements `IToolsProtocol` (AES403) and exports the `context7`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the multi-entry launcher writer
and pnpm post-copy flag hook are defined here.
"""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_constant import (
    CONTEXT7_LAUNCHER_ENTRIES,
    PNPM_DANGEROUS_ALLOW,
)
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
    dispatch_unit_op,
    write_node_launcher,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class Context7ToolsAdapter(IToolsProtocol):
    """Context7 actions behind the tools protocol (AES403 implementor)."""

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
        """Dispatch *op* against this file's context7 unit."""
        return dispatch_unit_op(self._units, op, spec, query, args, label="context7 adapter")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return f"Context7ToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Recipe (node lifecycle + per-tool hooks)
# ---------------------------------------------------------------------------
def _context7_write_launchers(app_dir: Path, is_update: bool) -> list[Path]:
    """Write one launcher per CONTEXT7_LAUNCHER_ENTRIES (warn on missing)."""
    created = []
    for lname, lentry in CONTEXT7_LAUNCHER_ENTRIES.items():
        target = app_dir / lentry
        if target.exists():
            created.append(write_node_launcher(lname, target))
        else:
            print(f"  Warning: entry not found {target}", file=sys.stderr)
    return created


def _context7_post_copy(app_dir: Path) -> None:
    ws = app_dir / "pnpm-workspace.yaml"
    if PNPM_DANGEROUS_ALLOW not in ws.read_text(encoding="utf-8", errors="replace"):
        with ws.open("a", encoding="utf-8") as f:
            f.write(f"\n{PNPM_DANGEROUS_ALLOW}: true\n")


CONFIG = ToolLifecycleConfig(
    lifecycle="node",
    src_rel="vendor/context7",
    app_name="context7",
    launchers=("context7-mcp", "ctx7"),
    ignores=(
        "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
        "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
    ),
    src_marker="pnpm-workspace.yaml",
    pin_reason="pnpm workspace (rebuild required)",
    satisfied_bin="context7-mcp",
    requires=("pnpm", "context7 is a pnpm workspace"),
    install_cmd=("pnpm", "install", "--frozen-lockfile"),
    build_cmd=("pnpm", "run", "build"),
    node_write_launchers_fn=_context7_write_launchers,
    node_post_copy_hook=_context7_post_copy,
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "context7": build_adapter_unit("context7", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "Context7ToolsAdapter",
]
