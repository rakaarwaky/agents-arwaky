"""qwen-web uninstaller — strict verbatim port of tools/uninstall/uninstall_qwen_web.py.

Every statement of the original standalone script is preserved; only the
import paths were swapped to the AES equivalents:
- from paths import repo_root           -> modules.shared.src.utility_paths
- from xdg import remove_tool_artifacts -> modules.shared.src.taxonomy_xdg_atomic_io
"""
from __future__ import annotations

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolUninstaller
from modules.shared.src.taxonomy_xdg_atomic_io import remove_tool_artifacts

ROOT = repo_root()

LAUNCHERS = ['qwen-web-arwaky', 'qwa', 'qwen-web-cli', 'qwen-web-mcp', 'qwc']


# ─── Block 1: Class Definition & Constructor ──────────────
class QwenWebUninstaller(IToolUninstaller):
    """AES facade over the verbatim original uninstall body."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    # ─── Block 2: Protocol ABC Method Implementation ──────────

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        rc = _uninstall()
        return UninstallResult(rc == 0, spec.id, "qwen-web uninstalled (launchers + data + config + cache)")

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
def _uninstall() -> int:
    print(">>> Uninstalling qwen-web...")
    remove_tool_artifacts("qwen-web", ['qwen-web-arwaky', 'qwa', 'qwen-web-cli', 'qwen-web-mcp', 'qwc'])
    print(">>> qwen-web uninstalled (launchers + data + config + cache).")
    return 0



