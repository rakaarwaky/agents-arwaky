"""
Contract: WorkflowAgentAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
"""

from taxonomy import FilePath, ObjectName


class WorkflowAgentOrchestratorAggregate:
    """Interface for WorkflowAgentOrchestrator."""

    _contract_name: ObjectName = ObjectName("WorkflowAgentOrchestratorAggregate")
    _compliance: FilePath | None = None

    @classmethod
    def get_contract_name(cls) -> ObjectName:
        return cls._contract_name
