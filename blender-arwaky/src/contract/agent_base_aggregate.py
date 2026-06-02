"""
Contract: AgentBaseAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
"""

from taxonomy import FilePath, ObjectName


class AgentBaseContainerAggregate:
    """Interface for AgentBaseContainer."""

    _contract_name: ObjectName = ObjectName("AgentBaseContainerAggregate")
    _compliance: FilePath | None = None

    @classmethod
    def get_contract_name(cls) -> ObjectName:
        return cls._contract_name
