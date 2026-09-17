"""Tool composition root — wires capabilities into the orchestrator."""
from __future__ import annotations

from modules.shared.src.tool.contract_tool_aggregate import IToolAggregate
from modules.runner.src.agent_runner_orchestrator import ToolOrchestrator
from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator
from modules.runner.src.capabilities_runner import ToolResolver
from modules.uninstaller.src.capabilities_uninstaller import ToolUninstaller
from modules.updater.src.capabilities_updater import ToolUpdater


class ToolContainer:
    """Wire the 4 tool capabilities to their contracts and construct the agent."""

    def __init__(self) -> None:
        resolver = ToolResolver()
        installer = InstallerOrchestrator()
        uninstaller = ToolUninstaller()
        updater = ToolUpdater(installer=installer)
        self._orchestrator = ToolOrchestrator(resolver, installer, updater, uninstaller)

    @property
    def aggregate(self) -> IToolAggregate:
        return self._orchestrator


def create_runner_feature() -> IToolAggregate:
    """Fully-wired tool feature aggregate."""
    return ToolContainer().aggregate
