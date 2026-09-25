"""Capability — fetch-mcp tool adapter (bun workspace recipe).

Implements `IToolsProtocol` (AES403) and exports the `fetch`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Recipe lives in `ToolLifecycleConfig`; the dual-dist python launcher
writer is defined here.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    bin_home,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_tools_constant import FETCH_CLI_ARGS, LAUNCHER_NAMES
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_tool_mechanics import (
    build_adapter_unit,
    dispatch_unit_op,
)


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class FetchToolsAdapter(IToolsProtocol):
    """fetch-mcp actions behind the tools protocol (AES403 implementor)."""

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
        """Dispatch *op* against this file's fetch unit."""
        return dispatch_unit_op(self._units, op, spec, query, args, label="fetch adapter")

    # ─── Block 3: Dunder Methods ─────────────────────────────────────
    def __repr__(self) -> str:
        return f"FetchToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Recipe (node lifecycle + dual-dist launcher writer)
# ---------------------------------------------------------------------------
def _fetch_write_launchers(app_dir: Path, is_update: bool) -> list[Path]:
    """Write python launchers routing argv between dist/index.js and dist/cli.js."""
    index_js = app_dir / "dist/index.js"
    cli_js = app_dir / "dist/cli.js"
    if not index_js.exists() or not cli_js.exists():
        raise (ToolUpdateError if is_update else FileNotFoundError)(
            f"build output incomplete ({index_js}, {cli_js})")
    ensure_bin_home()
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        f'index_js = r"{index_js}"\n'
        f'cli_js = r"{cli_js}"\n'
        "cli = " + repr(sorted(FETCH_CLI_ARGS)) + "\n"
        "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
        "env = os.environ.copy()\n"
        'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
    )
    artifacts = []
    for lname in ("fetch-mcp", "mcp-fetch"):
        launcher = bin_home() / lname
        launcher.write_text(content, encoding="utf-8")
        launcher.chmod(0o755)
        artifacts.append(launcher)
        print(f"  -> {launcher}")
    warn_if_bin_not_on_path()
    return artifacts


CONFIG = ToolLifecycleConfig(
    lifecycle="node",
    src_rel="vendor/fetch-mcp",
    app_name="fetch-mcp",
    launchers=tuple(LAUNCHER_NAMES["fetch"]),
    pin_reason="bun workspace (rebuild required)",
    satisfied_bin="fetch-mcp",
    requires=("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"),
    install_cmd=("bun", "install", "--frozen-lockfile"),
    build_cmd=("bun", "run", "build"),
    node_write_launchers_fn=_fetch_write_launchers,
)

#: tool_id → unit (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "fetch": build_adapter_unit("fetch", CONFIG),
}


__all__ = [
    "ADAPTER_UNITS",
    "FetchToolsAdapter",
]
