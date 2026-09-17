"""context7 uninstaller — port of tools/uninstall/uninstall_context7.py.

Removes context7's launchers + XDG data/config/cache artifacts via the
shared remove_tool_artifacts helper (per-tool launcher list preserved from
the original script).
"""
from __future__ import annotations

from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_protocol import IToolUninstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import remove_tool_artifacts


LAUNCHERS = ['context7-mcp', 'ctx7']


class Context7Uninstaller(IToolUninstaller):
    """Remove context7's launchers + XDG artifacts."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()


    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        print(f">>> Uninstalling context7...")

        remove_tool_artifacts("context7", LAUNCHERS)
        return UninstallResult(True, spec.id, "context7 uninstalled (launchers + data + config + cache)")
