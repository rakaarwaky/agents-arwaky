"""
Contract: CoreAgentAggregate (AES _aggregate suffix).
Specialized structural contract for the agent layer.
"""

from abc import ABC, abstractmethod

from taxonomy import (
    ActionName,
    Details,
    DomainRef,
    FilePath,
    FormatRef,
    JobId,
    ObjectName,
    Prompt,
    ProviderName,
    SectionRef,
    SkillName,
)


class CoreAgentOrchestratorAggregate(ABC):
    """Interface for CoreAgentOrchestrator."""

    _contract_name: ObjectName = ObjectName("CoreAgentOrchestratorAggregate")
    _compliance: FilePath | None = None

    @classmethod
    def get_contract_name(cls) -> ObjectName:
        return cls._contract_name

    @abstractmethod
    async def execute_action(self, action: ActionName, args: Details | None = None) -> Prompt:
        """Execute an action via the capabilities layer."""
        ...

    @abstractmethod
    def list_commands(self, domain: DomainRef | None = None, format: FormatRef | None = None) -> Prompt:
        """List commands registered in the catalog."""
        ...

    @abstractmethod
    async def check_status(self, provider: ProviderName, job_id: JobId) -> Prompt:
        """Check status of a background generation job."""
        ...

    @abstractmethod
    def health_check(self) -> Prompt:
        """Check system connectivity and subsystem health."""
        ...

    @abstractmethod
    def read_skill_context(self, skill_name: SkillName, section: SectionRef | None = None) -> Prompt:
        """Read SKILL.md documentation details."""
        ...
