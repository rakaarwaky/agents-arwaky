"""fetch-mcp uninstaller — port of tools/uninstall/uninstall_fetch_mcp.py.

Removes fetch-mcp's launchers + XDG data/config/cache artifacts via the
shared remove_tool_artifacts helper (per-tool launcher list preserved from
the original script).
"""
from __future__ import annotations

from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_protocol import IToolUninstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import remove_tool_artifacts


LAUNCHERS = ['fetch-mcp', 'mcp-fetch']


class FetchMcpUninstaller(IToolUninstaller):
    """Remove fetch-mcp's launchers + XDG artifacts."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()


    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        print(f">>> Uninstalling fetch-mcp...")

        remove_tool_artifacts("fetch-mcp", LAUNCHERS)
        return UninstallResult(True, spec.id, "fetch-mcp uninstalled (launchers + data + config + cache)")
