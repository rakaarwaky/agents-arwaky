"""
Contract: Port interface for AI generation providers (Hyper3D, Hunyuan3D, etc.).

Defines the contract for text-to-3D generation, job status polling, and importing results.
AES Port layer — depends only on taxonomy entities and provider IO DTOs.
"""

from abc import ABC, abstractmethod

from taxonomy import (
    GenerationStartRequestVO,
    GenerationStartResponseVO,
    GenerationStatusRequestVO,
    GenerationStatusResponseVO,
    ImportGeneratedAssetRequestVO,
    ImportGeneratedAssetResponseVO,
)


class GenerationProviderPort(ABC):
    """Port interface for AI 3D generation services."""

    @abstractmethod
    async def start_generation(self, request: GenerationStartRequestVO) -> GenerationStartResponseVO:
        """Start a generation job from text prompt. Returns job acceptance response."""
        pass

    @abstractmethod
    async def poll_generation(self, request: GenerationStatusRequestVO) -> GenerationStatusResponseVO:
        """Poll the status of a generation job. Returns current status."""
        pass

    @abstractmethod
    async def import_generated_asset(self, request: ImportGeneratedAssetRequestVO) -> ImportGeneratedAssetResponseVO:
        """Import a completed generation result into Blender as an object."""
        pass
