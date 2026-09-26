"""Capability — ponytail tool adapter (npm workspace recipe).

Implements `IToolsAdapterProtocol` (AES403) and exports the `ponytail`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the launcher writer is the
generic `build_adapter_unit` default and only the npm-ci post-copy
hook is defined here.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    ROOT,
    build_adapter_unit,
    run,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class PonytailToolsAdapter(IToolsAdapterProtocol):
    """Ponytail actions behind the tools adapter protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def _unit_for(self, spec: ToolSpec) -> AdapterUnit:
        """Look up the adapter unit that owns *spec*."""
        unit = self._units.get(spec.id)
        if unit is None:
            raise ToolUpdateError(f"ponytail adapter has no unit for {spec.id!r}")
        return unit

    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when *spec*'s unit reports installed state."""
        return self._unit_for(spec).satisfied(spec, root)

    def is_pin_satisfied(self, spec: ToolSpec, root: Path | None = None) -> tuple[bool, str]:
        """Return (satisfied, reason) against the manifest pin."""
        return self._unit_for(spec).is_pin_satisfied(spec, root or ROOT)

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Return the paths this adapter owns for *spec*."""
        return list(self._unit_for(spec).owned_paths(spec, root or ROOT) or [])

    def install(self, spec: ToolSpec, root: Path, *, daemons: object | None = None) -> list[Path]:
        """Install or build *spec*; return the created paths."""
        unit = self._unit_for(spec)
        try:
            return list(unit.install(spec, root, daemons=daemons) or [])
        except TypeError:
            return list(unit.install(spec, root) or [])

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        """Update *spec* to the manifest pin; return the rebuilt paths."""
        return list(self._unit_for(spec).update(spec, root) or [])

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
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
