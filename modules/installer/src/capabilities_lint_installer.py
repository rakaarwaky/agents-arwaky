"""Lint-arwaky installer capability (cargo runner)."""
from __future__ import annotations

from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec

from modules.installer.src.utility_installer_base import InstallerBase
from modules.installer.src.utility_runner_strategies import install_cargo


class LintInstaller(IToolInstaller):
    """Build internal/lint-arwaky with cargo --release into XDG cache."""

    def __init__(self, root=None) -> None:
        self._base = InstallerBase(root)

    def install(self, spec: ToolSpec) -> InstallResult:
        self._base.prepare_env()
        return install_cargo(self._base, spec)
