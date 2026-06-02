"""Generator: AI Generation business logic (multi-provider)."""

import logging

from contract import GenerationProtocol, GenerationProviderPort
from taxonomy import (
    ErrorMessage,
    GenerationStartRequestVO,
    GenerationStatusRequestVO,
    JobId,
    JobStatus,
    Prompt,
    ProviderError,
    ProviderName,
)

logger = logging.getLogger("BlenderMCPServer")


class AiGenerateGenerator(GenerationProtocol):
    """Business logic for AI generation across providers."""

    def __init__(self, providers: dict[str, GenerationProviderPort]):
        self.providers = providers

    async def start_generation(self, provider_name: ProviderName, prompt: Prompt) -> JobId:
        provider = self.providers.get(str(provider_name))
        if not provider:
            raise ProviderError(ErrorMessage(f"Generation provider {provider_name} not found"))
        request = GenerationStartRequestVO(prompt=prompt)
        response = await provider.start_generation(request)
        return response.job_id

    async def check_status(self, provider_name: ProviderName, job_id: JobId) -> JobStatus:
        provider = self.providers.get(str(provider_name))
        if not provider:
            raise ProviderError(ErrorMessage(f"Generation provider {provider_name} not found"))
        request = GenerationStatusRequestVO(job_id=job_id)
        response = await provider.poll_generation(request)
        return JobStatus(
            job_id=job_id,
            status=response.status,
            progress=response.progress,
            error=response.error,
        )
