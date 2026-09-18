"""Runner feature: execute tool binaries via feature orchestrator.

Public API:
- ToolOrchestrator (agent): feature orchestrator
- ToolResolver (capabilities): tool binary resolution
- ToolContainer: feature container
- cmd_tool_surface: CLI command handlers
- IToolAggregate (contract): feature aggregate protocol
"""
from __future__ import annotations

from modules.runner.src.agent_runner_orchestrator import RunnerOrchestrator, ToolOrchestrator
from modules.runner.src.contract_runner_base import RunnerBase
from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate
from modules.runner.src.root_runner_container import ToolContainer, create_runner_feature
from modules.runner.src.agent_runner_verb import cmd_install, cmd_list, cmd_run, cmd_tool, cmd_uninstall, cmd_update

__all__ = [
    "IToolAggregate",
    "ToolContainer",
    "ToolOrchestrator",
    "RunnerOrchestrator",
    "cmd_install",
    "cmd_list",
    "cmd_run",
    "cmd_tool",
    "cmd_uninstall",
    "cmd_update",
    "create_runner_feature",
    "RunnerBase",
]
