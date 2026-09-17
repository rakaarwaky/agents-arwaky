"""lint-arwaky uninstaller — port of tools/uninstall/uninstall_lint.py.

Removes lint-arwaky's launchers + XDG data/config/cache artifacts via the
shared remove_tool_artifacts helper (per-tool launcher list preserved from
the original script).
"""
from __future__ import annotations

from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_protocol import IToolUninstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import remove_tool_artifacts


LAUNCHERS = ['lint-arwaky', 'la', 'lint-arwaky-cli', 'lint-arwaky-mcp', 'lint-arwaky-tui', 'lac']


class LintUninstaller(IToolUninstaller):
    """Remove lint-arwaky's launchers + XDG artifacts."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()


    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        print(f">>> Uninstalling lint-arwaky...")

        remove_tool_artifacts("lint-arwaky", LAUNCHERS)
        return UninstallResult(True, spec.id, "lint-arwaky uninstalled (launchers + data + config + cache)")
