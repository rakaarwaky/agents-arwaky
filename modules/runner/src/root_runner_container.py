"""Tool composition root — wires capabilities into the orchestrator."""
from __future__ import annotations

from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate
from modules.runner.src.agent_runner_orchestrator import RunnerOrchestrator, ToolOrchestrator
from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator
from modules.uninstaller.src.agent_uninstaller_orchestrator import UninstallerOrchestrator
from modules.updater.src.agent_updater_orchestrator import UpdaterOrchestrator


class ToolContainer:
    """Wire the 4 tool capabilities to their contracts and construct the agent."""

    def __init__(self) -> None:
        from modules.installer.src.root_tool_installer_registry import build_installer_registry
        from modules.runner.src.root_tool_runner_registry import RUNNER_REGISTRY
        from modules.uninstaller.src.root_tool_uninstaller_registry import build_uninstaller_registry
        from modules.updater.src.root_tool_updater_registry import build_updater_registry

        resolver = RunnerOrchestrator(registry=RUNNER_REGISTRY)
        installer = InstallerOrchestrator(registry=build_installer_registry())
        uninstaller = UninstallerOrchestrator(registry=build_uninstaller_registry())
        updater = UpdaterOrchestrator(registry=build_updater_registry())
        self._orchestrator = ToolOrchestrator(resolver, installer, updater, uninstaller)

    @property
    def aggregate(self) -> IToolAggregate:
        return self._orchestrator


def create_runner_feature() -> IToolAggregate:
    """Fully-wired tool feature aggregate."""
    return ToolContainer().aggregate
