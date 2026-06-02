"""
Contract: Port interface for Hyper3D Rodin generation tool operations.

Defines the contract for Hyper3D-specific tool calls (status, generate via
text/images, poll, import). Separate from GenerationProviderPort because
these are direct Blender-addon-mediated wrappers, not generic adapters.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import BBoxIntegers, CoordinateList, ObjectName, Prompt, StatusString, StringList, TaskUuid


class Hyper3dToolPort(ABC):
    """Port interface for Hyper3D Rodin generation tool operations via Blender addon."""

    @abstractmethod
    def get_hyper3d_status(self) -> StatusString:
        """Check if Hyper3D Rodin integration is enabled."""
        pass

    @abstractmethod
    def generate_hyper3d_model_via_text(
        self, text_prompt: Prompt, bbox_condition: CoordinateList | None = None
    ) -> StatusString:
        """Generate a 3D asset from text description."""
        pass

    @abstractmethod
    def generate_hyper3d_model_via_images(
        self,
        input_image_paths: StringList | None = None,
        input_image_urls: StringList | None = None,
        bbox_condition: CoordinateList | None = None,
    ) -> StatusString:
        """Generate a 3D asset from images."""
        pass

    @abstractmethod
    def poll_rodin_job_status(
        self, subscription_key: StatusString | None = None, request_id: StatusString | None = None
    ) -> StatusString:
        """Poll the status of a Hyper3D generation job."""
        pass

    @abstractmethod
    def import_generated_asset(
        self, name: ObjectName, task_uuid: TaskUuid | None = None, request_id: StatusString | None = None
    ) -> StatusString:
        """Import a generated Hyper3D asset into Blender."""
        pass

    @abstractmethod
    def process_bbox(self, original_bbox: CoordinateList | None) -> BBoxIntegers | None:
        """Process bounding box condition values."""
        pass
