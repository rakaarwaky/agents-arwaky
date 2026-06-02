"""
Contract: Execute Action Protocol (AES _protocol suffix).
"""

from abc import ABC, abstractmethod

from taxonomy import ActionName, Details, Prompt


class ExecuteActionProtocol(ABC):
    """Entry point interface for executing any BlenderMCP action."""

    @abstractmethod
    async def execute(self, action: ActionName, args: Details | None = None) -> Prompt:
        """Dispatch an action to the orchestrator."""
        pass
