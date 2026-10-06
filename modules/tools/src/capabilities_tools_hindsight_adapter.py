"""Capability — hindsight tool adapter (uv_project recipe).

Exports the ``hindsight``
``AdapterUnit`` merged into ``TOOLS_REGISTRY`` by the root container.
Recipe lives in ``ToolLifecycleConfig``; shared mechanics live in
``utility_tool_mechanics``.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import (
    AdapterUnit,
    PinCheck,
    ToolLifecycleConfig,
    ToolPaths,
)
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
)
from modules.shared.src.utility_tools_adapter_body import (
    install_unit,
    is_pin_satisfied_unit,
    owned_paths_unit,
    satisfied_unit,
    update_unit,
)


# ─── Block 1: Class Definition & Constructor ───
class HindsightToolsAdapter(IToolsAdapterProtocol):
    """hindsight actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'hindsight'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        self._units = dict(ADAPTER_UNITS) if units is None else units

    # ─── Block 2: Protocol Method Implementation ───
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

# ─── Block 3: Dunder Methods, Factories & Helpers ───
config = ToolLifecycleConfig(
    lifecycle="uv_project",
    src_rel="vendor/hindsight",
    tool_name="hindsight",
    launchers=(
        ("hindsight", "hindsight-api"),
        ("hindsight-local-mcp", "hindsight-local-mcp"),
        ("hindsight-local-mcp-server", "hindsight-local-mcp"),
    ),
    pin_reason="uv workspace (rebuild required)",
    satisfied_bin="hindsight-local-mcp",
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "hindsight": build_adapter_unit("hindsight", config),
}
