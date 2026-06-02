"""
Contract: AI Generation Contract (ABC based).
"""

from abc import ABC, abstractmethod

from taxonomy import JobId, JobStatus, Prompt, ProviderName


class GenerationProtocol(ABC):
    """Business logic interface for AI generation across providers."""

    @abstractmethod
    async def start_generation(self, provider_name: ProviderName, prompt: Prompt) -> JobId:
        """Start a generation job on the specified provider."""
        pass

    @abstractmethod
    async def check_status(self, provider_name: ProviderName, job_id: JobId) -> JobStatus:
        """Poll the status of a generation job."""
        pass
