"""
Contract: Port interface for scene inspection in Blender.

Defines the contract for retrieving scene info, object info, and cleaning up.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import ObjectName, Prompt


class SceneInspectionPort(ABC):
    """Port interface for inspecting and cleaning the Blender scene."""

    @abstractmethod
    async def get_scene_info(self) -> Prompt:
        """Get detailed information about the current Blender scene."""
        pass

    @abstractmethod
    async def get_object_info(self, object_name: ObjectName) -> Prompt:
        """Get detailed information about a specific object by name."""
        pass

    @abstractmethod
    async def cleanup_scene(self) -> Prompt:
        """Remove all objects from the scene."""
        pass
