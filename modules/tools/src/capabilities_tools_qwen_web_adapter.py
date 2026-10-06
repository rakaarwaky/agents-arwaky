"""Capability — qwen-web tool adapter (uv_venv + Playwright recipe).

Exports the `qwen-web`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the Playwright/XDG post-install
hook and shared mechanics live in this file /
`utility_tool_mechanics`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)
from modules.shared.src.taxonomy_tools_constant import QWEN_ROLE_DIRS, QWEN_TOOL_NAME
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


# ─── Block 1: Class Definition & Constructor ──────────────
class QwenWebToolsAdapter(IToolsAdapterProtocol):
    """qwen-web actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'qwen-web'

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




# ---------------------------------------------------------------------------
# Recipe (uv_venv lifecycle + Playwright post-install)
# ---------------------------------------------------------------------------

# ─── Block 3: Dunder Methods, Factories & Helpers ──────────

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

config = ToolLifecycleConfig(
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
    "qwen-web-arwaky": build_adapter_unit("qwen-web-arwaky", config),
}

__all__ = [
    "ADAPTER_UNITS",
    "QwenWebToolsAdapter",
]
