"""
Contract: SystemPromptAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
"""

from taxonomy import FilePath, ObjectName


class SystemPromptManagerAggregate:
    """Interface for SystemPromptManager."""

    _contract_name: ObjectName = ObjectName("SystemPromptManagerAggregate")
    _compliance: FilePath | None = None

    @classmethod
    def get_contract_name(cls) -> ObjectName:
        return cls._contract_name
