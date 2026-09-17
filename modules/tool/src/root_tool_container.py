"""Tool composition root — wires capabilities into the orchestrator."""
from __future__ import annotations

from modules.shared.src.tool.contract_tool_aggregate import IToolAggregate
from modules.tool.src.agent_tool_orchestrator import ToolOrchestrator
from modules.tool.src.capabilities_tool_install import ToolInstaller
from modules.tool.src.capabilities_tool_resolver import ToolResolver
from modules.tool.src.capabilities_tool_uninstall import ToolUninstaller
from modules.tool.src.capabilities_tool_update import ToolUpdater


class ToolContainer:
    """Wire the 4 tool capabilities to their contracts and construct the agent."""

    def __init__(self) -> None:
        resolver = ToolResolver()
        installer = ToolInstaller()
        uninstaller = ToolUninstaller()
        updater = ToolUpdater(installer=installer)
        self._orchestrator = ToolOrchestrator(resolver, installer, updater, uninstaller)

    @property
    def aggregate(self) -> IToolAggregate:
        return self._orchestrator


def create_tool_feature() -> IToolAggregate:
    """Fully-wired tool feature aggregate."""
    return ToolContainer().aggregate
