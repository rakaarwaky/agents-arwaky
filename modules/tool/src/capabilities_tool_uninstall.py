"""Tool uninstall capability — remove launchers and XDG artifacts."""
from __future__ import annotations

import shutil
from pathlib import Path

from modules.shared.src.logging.utility_logging import ok
from modules.shared.src.tool.contract_tool_protocol import IToolUninstaller
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.xdg.utility_xdg_atomic_io import remove_tool_artifacts


def _launcher_names(spec: ToolSpec) -> list[str]:
    """Every launcher an install may have written for this spec."""
    names = [spec.binary]
    if spec.mcp_binary and spec.mcp_binary != spec.binary:
        names.append(spec.mcp_binary)
    if spec.alias:
        names.append(spec.alias)
    return names


class ToolUninstaller(IToolUninstaller):
    """Remove bin launchers + XDG data/config/cache, ported from tools/uninstall/*.

    # Block 1: Constructor
    # Block 2: Launcher set resolution
    # Block 3: Artifact removal + result shaping
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self) -> None:
        pass

    # -- Block 2: Launcher set resolution ----------------------------------------
    def _launchers(self, spec: ToolSpec) -> list[str]:
        return _launcher_names(spec)

    # -- Block 3: Artifact removal + result shaping -------------------------------
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        tool_name = spec.binary or spec.id
        remove_tool_artifacts(tool_name, self._launchers(spec))
        shutil.rmtree(Path.home() / ".cache" / spec.id, ignore_errors=True)
        ok(f"Uninstalled {spec.id} (launchers + data + config + cache)")
        return UninstallResult(True, spec.id, f"removed artifacts for {tool_name}")
