"""context7 uninstaller — strict verbatim port of tools/uninstall/uninstall_context7.py.

Every statement of the original standalone script is preserved; only the
import paths were swapped to the AES equivalents:
- from paths import repo_root           -> modules.shared.src.utility_paths
- from xdg import remove_tool_artifacts -> modules.shared.src.utility_xdg_atomic_io
"""
from __future__ import annotations

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.uninstaller.src.contract_tool_uninstaller import IToolUninstaller
from modules.shared.src.utility_xdg_atomic_io import remove_tool_artifacts

ROOT = repo_root()

LAUNCHERS = ['context7-mcp', 'ctx7']


def _uninstall() -> int:
    print(">>> Uninstalling context7...")
    remove_tool_artifacts("context7", ['context7-mcp', 'ctx7'])
    print(">>> context7 uninstalled (launchers + data + config + cache).")
    return 0


class Context7Uninstaller(IToolUninstaller):
    """AES facade over the verbatim original uninstall body."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        rc = _uninstall()
        return UninstallResult(rc == 0, spec.id, "context7 uninstalled (launchers + data + config + cache)")
