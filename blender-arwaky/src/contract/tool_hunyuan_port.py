"""
Contract: Port interface for Hunyuan3D generation tool operations.

Defines the contract for Hunyuan3D-specific tool calls (status, generate,
poll, import). Separate from GenerationProviderPort because these are
direct Blender-addon-mediated wrappers, not generic adapters.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import JobId, ObjectName, Prompt, ResultUrl, StatusString


class HunyuanToolPort(ABC):
    """Port interface for Hunyuan3D generation tool operations via Blender addon."""

    @abstractmethod
    def get_hunyuan3d_status(self) -> StatusString:
        """Check if Hunyuan3D integration is enabled."""
        pass

    @abstractmethod
    def generate_hunyuan3d_model(
        self, text_prompt: Prompt | None = None, input_image_url: ResultUrl | None = None
    ) -> StatusString:
        """Generate a 3D asset using Hunyuan3D from text and/or image."""
        pass

    @abstractmethod
    def poll_hunyuan_job_status(self, job_id: JobId | None = None) -> StatusString:
        """Poll the status of a Hunyuan3D generation job."""
        pass

    @abstractmethod
    def import_generated_asset_hunyuan(self, name: ObjectName, zip_file_url: ResultUrl) -> StatusString:
        """Import a generated Hunyuan3D asset into Blender."""
        pass
