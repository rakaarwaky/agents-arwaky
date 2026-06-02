"""
Contract: GenerationExpertAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
"""

from taxonomy import FilePath, StatusString


class GenerationExpertOrchestratorAggregate:
    """Interface for GenerationExpertOrchestrator."""

    _contract_name: StatusString = StatusString("GenerationExpertOrchestratorAggregate")
    _compliance: FilePath | None = None

    @classmethod
    def get_contract_name(cls) -> StatusString:
        return cls._contract_name
