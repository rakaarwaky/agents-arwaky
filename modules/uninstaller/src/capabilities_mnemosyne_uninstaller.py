"""mnemosyne uninstaller — strict verbatim port of tools/uninstall/uninstall_mnemosyne.py.

Every statement of the original standalone script is preserved; only the
import paths were swapped to the AES equivalents:
- from paths import repo_root           -> modules.shared.src.paths.utility_paths
- from xdg import remove_tool_artifacts -> modules.shared.src.xdg.utility_xdg_atomic_io
"""
from __future__ import annotations

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.tool.contract_tool_protocol import IToolUninstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import remove_tool_artifacts

ROOT = repo_root()

LAUNCHERS = ['mnemosyne', 'mnemosyne-mcp']


def _uninstall() -> int:
    print(">>> Uninstalling mnemosyne...")
    remove_tool_artifacts("mnemosyne", ['mnemosyne', 'mnemosyne-mcp'])
    print(">>> mnemosyne uninstalled (launchers + data + config + cache).")
    return 0


class MnemosyneUninstaller(IToolUninstaller):
    """AES facade over the verbatim original uninstall body."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        rc = _uninstall()
        return UninstallResult(rc == 0, spec.id, "mnemosyne uninstalled (launchers + data + config + cache)")
