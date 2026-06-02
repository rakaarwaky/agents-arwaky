"""
Contract: RefinementExpertAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
"""

from taxonomy import FilePath, StatusString


class RefinementExpertOrchestratorAggregate:
    """Interface for RefinementExpertOrchestrator."""

    _contract_name: StatusString = StatusString("RefinementExpertOrchestratorAggregate")
    _compliance: FilePath | None = None

    @classmethod
    def get_contract_name(cls) -> StatusString:
        return cls._contract_name
