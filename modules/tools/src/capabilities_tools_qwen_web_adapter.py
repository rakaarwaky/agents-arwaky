"""Capability — qwen-web tool adapter (uv_venv + Playwright recipe).

Implements `IToolsAdapterProtocol` (AES403) and exports the `qwen-web`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the Playwright/XDG post-install
hook and shared mechanics live in this file /
`utility_tool_mechanics`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)
from modules.shared.src.taxonomy_tools_constant import QWEN_ROLE_DIRS, QWEN_TOOL_NAME
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    ROOT,
    build_adapter_unit,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class QwenWebToolsAdapter(IToolsAdapterProtocol):
    """qwen-web actions behind the tools adapter protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def _unit_for(self, spec: ToolSpec) -> AdapterUnit:
        """Look up the adapter unit that owns *spec*."""
        unit = self._units.get(spec.id)
        if unit is None:
            raise ToolUpdateError(f"qwen-web adapter has no unit for {spec.id!r}")
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
        return f"QwenWebToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Recipe (uv_venv lifecycle + Playwright post-install)
# ---------------------------------------------------------------------------
def _qwen_post_install(python_bin, source) -> None:
    print("  [install] Installing Playwright Chromium...")
    subprocess.run([str(python_bin), "-m", "playwright", "install", "chromium"], check=True)
    data_dir = tool_data_dir(QWEN_TOOL_NAME)
    state_dir = tool_state_dir(QWEN_TOOL_NAME)
    cache_dir = tool_cache_dir(QWEN_TOOL_NAME)
    for role in QWEN_ROLE_DIRS:
        (data_dir / "input" / role / "done").mkdir(parents=True, exist_ok=True)
        (data_dir / "input" / role / "failed").mkdir(parents=True, exist_ok=True)
    (data_dir / "output").mkdir(parents=True, exist_ok=True)
    (data_dir / "qwen_session").mkdir(parents=True, exist_ok=True)
    (state_dir / "log").mkdir(parents=True, exist_ok=True)
    (cache_dir / ".processing").mkdir(parents=True, exist_ok=True)
    print(f"  [ok] Data: {data_dir}")
    print(f"  [ok] State: {state_dir}")
    print(f"  [ok] Cache: {cache_dir}")


CONFIG = ToolLifecycleConfig(
    lifecycle="uv_venv",
    src_rel=f"internal/{QWEN_TOOL_NAME}-arwaky",
    tool_name=QWEN_TOOL_NAME,
    launchers=(
        ("qwen-web-arwaky", "qwen-web-arwaky"),
        ("qwa", "qwen-web-arwaky"),
        ("qwen-web-cli", "qwen-web-arwaky"),
        ("qwen-web-mcp", "qwen-web-mcp"),
        ("qwc", "qwen-web-arwaky"),
    ),
    pin_reason="venv/pip + Playwright (rebuild required)",
    satisfied_bin="qwen-web-arwaky",
    init_message="Run 'qwc init' to setup workspace symlinks",
    post_install_hook=_qwen_post_install,
    extra_paths_fn=lambda: [
        tool_config_dir(QWEN_TOOL_NAME),
        tool_state_dir(QWEN_TOOL_NAME),
        tool_cache_dir(QWEN_TOOL_NAME),
    ],
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "qwen-web-arwaky": build_adapter_unit("qwen-web-arwaky", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "QwenWebToolsAdapter",
]
