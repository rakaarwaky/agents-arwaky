"""Context7 (generic npm/pnpm runner)."""
from __future__ import annotations

from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec

from modules.installer.src.utility_installer_base import InstallerBase
from modules.installer.src.utility_runner_strategies import install_generic


class Context7Installer(IToolInstaller):
    """Install Installer via copy-to-XDG + pnpm/npm build + node launcher."""

    def __init__(self, root=None) -> None:
        self._base = InstallerBase(root)

    def install(self, spec: ToolSpec) -> InstallResult:
        self._base.prepare_env()
        return install_generic(self._base, spec)
