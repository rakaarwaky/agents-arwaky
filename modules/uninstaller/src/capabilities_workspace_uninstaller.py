"""google-workspace-mcp uninstaller — strict verbatim port of tools/uninstall/uninstall_workspace.py.

Every statement of the original standalone script is preserved; only the
import paths were swapped to the AES equivalents:
- from paths import repo_root           -> modules.shared.src.common.utility_paths
- from xdg import remove_tool_artifacts -> modules.shared.src.xdg.utility_xdg_atomic_io
"""
from __future__ import annotations

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.uninstaller.src.contract_tool_uninstaller import IToolUninstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import remove_tool_artifacts

ROOT = repo_root()

LAUNCHERS = ['workspace-mcp', 'google-workspace-mcp']


def _uninstall() -> int:
    print(">>> Uninstalling google-workspace-mcp...")
    remove_tool_artifacts("google-workspace-mcp", ['workspace-mcp', 'google-workspace-mcp'])
    print(">>> google-workspace-mcp uninstalled (launchers + data + config + cache).")
    return 0


class WorkspaceUninstaller(IToolUninstaller):
    """AES facade over the verbatim original uninstall body."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        rc = _uninstall()
        return UninstallResult(rc == 0, spec.id, "google-workspace-mcp uninstalled (launchers + data + config + cache)")
