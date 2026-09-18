"""Tool composition root — wires capabilities into the orchestrator."""
from __future__ import annotations

from modules.runner.src.contract_tool_runner import IToolAggregate
from modules.runner.src.agent_runner_orchestrator import ToolOrchestrator
from modules.runner.src.capabilities_runner import ToolResolver
from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator
from modules.uninstaller.src.agent_uninstaller_orchestrator import UninstallerOrchestrator
from modules.updater.src.agent_updater_orchestrator import UpdaterOrchestrator


class ToolContainer:
    """Wire the 4 tool capabilities to their contracts and construct the agent."""

    def __init__(self) -> None:
        resolver = ToolResolver()
        installer = InstallerOrchestrator()
        uninstaller = UninstallerOrchestrator()
        updater = UpdaterOrchestrator()
        self._orchestrator = ToolOrchestrator(resolver, installer, updater, uninstaller)

    @property
    def aggregate(self) -> IToolAggregate:
        return self._orchestrator


def create_runner_feature() -> IToolAggregate:
    """Fully-wired tool feature aggregate."""
    return ToolContainer().aggregate
