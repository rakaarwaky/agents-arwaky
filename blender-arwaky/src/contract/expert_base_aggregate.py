"""
Contract: ExpertBaseAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
Contains the generic execute() entry point (formerly ExpertOperateProtocol).
"""

from abc import ABC, abstractmethod

from taxonomy import Details, FilePath, StatusString


class ExpertBaseOrchestratorAggregate(ABC):
    """Interface for ExpertBaseOrchestrator."""

    _contract_name: StatusString = StatusString("ExpertBaseOrchestratorAggregate")
    _compliance: FilePath | None = None

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Details:
        """Main entry point for the expert's primary task."""
        pass

    @classmethod
    def get_contract_name(cls) -> StatusString:
        return cls._contract_name
