"""
Contract: AgentDiContainerAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
"""

from abc import ABC, abstractmethod

from taxonomy import FilePath, ObjectName

from .command_catalog_port import CommandCatalogPort
from .core_agent_aggregate import CoreAgentOrchestratorAggregate
from .execute_action_protocol import ExecuteActionProtocol


class AgentDiContainerAggregate(ABC):
    """Interface for AgentDiContainer."""

    _contract_name: ObjectName = ObjectName("AgentDiContainerAggregate")
    _compliance: FilePath | None = None

    @classmethod
    def get_contract_name(cls) -> ObjectName:
        return cls._contract_name

    @property
    @abstractmethod
    def command_catalog(self) -> CommandCatalogPort:
        """Return the command catalog port for surface-layer discovery."""
        ...

    @property
    @abstractmethod
    def action_execute_capability(self) -> ExecuteActionProtocol:
        """Return the action executor for surface-layer dispatch."""
        ...

    @property
    @abstractmethod
    def core_agent_orchestrator(self) -> CoreAgentOrchestratorAggregate:
        """Return the core agent orchestrator (Palais)."""
        ...
