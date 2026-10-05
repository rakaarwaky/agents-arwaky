"""Capability — context7 tool adapter (pnpm workspace recipe).

Exports the `context7`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the multi-entry launcher writer
and pnpm post-copy flag hook are defined here.
"""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_constant import (
    CONTEXT7_LAUNCHER_ENTRIES,
    PNPM_DANGEROUS_ALLOW,
)
from modules.shared.src.taxonomy_tools_vo import (
    AdapterUnit,
    PinCheck,
    ToolLifecycleConfig,
    ToolPaths,
)
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
    write_node_launcher,
)
from modules.shared.src.utility_tools_adapter_body import (
    install_unit,
    is_pin_satisfied_unit,
    owned_paths_unit,
    satisfied_unit,
    update_unit,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class Context7ToolsAdapter(IToolsAdapterProtocol):
    """context7 actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'context7'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        self._units = dict(ADAPTER_UNITS) if units is None else units



    # ─── Block 2: Protocol Method Implementation ──────────────
    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when the installed binary satisfies the manifest."""
        return satisfied_unit(self._units, spec, self._display, root)

    def is_pin_satisfied(self, spec: ToolSpec, root: Path | None = None) -> PinCheck:
        """Return ``(satisfied, reason)`` against the manifest pin."""
        return is_pin_satisfied_unit(self._units, spec, self._display, root)

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> ToolPaths:
        """Return the paths this adapter's install owns for *spec*."""
        return owned_paths_unit(self._units, spec, self._display, root)

    def install(self, spec: ToolSpec, root: Path, *, daemons: object | None = None) -> ToolPaths:
        """Install or build *spec* into *root*; return the created paths."""
        return install_unit(self._units, spec, root, self._display, daemons=daemons)

    def update(self, spec: ToolSpec, root: Path) -> ToolPaths:
        """Update *spec* to the manifest pin; return the rebuilt paths."""
        return update_unit(self._units, spec, root, self._display)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────

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

config = ToolLifecycleConfig(
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
    "context7": build_adapter_unit("context7", config),
}

__all__ = [
    "ADAPTER_UNITS",
    "Context7ToolsAdapter",
]
