"""
Contract: Workflow Protocol (AES _protocol suffix).
"""

from abc import ABC, abstractmethod

from taxonomy import Prompt, ProviderName, SuccessFlag


class WorkflowProtocol(ABC):
    """Business logic interface for complex multi-step workflows."""

    @abstractmethod
    async def create_basic_scene(self, prompt: Prompt) -> SuccessFlag:
        """Create a basic scene."""
        pass

    @abstractmethod
    async def generate_and_import_ai_asset(self, provider_name: ProviderName, prompt: Prompt) -> Prompt:
        """Execute the full generation-to-import pipeline."""
        pass
