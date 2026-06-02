"""
Contract: Port interface for Blender socket adapter.

This port defines the interface that all Blender connection adapters must implement.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import BlenderObject, ImageBytes, MaxSize, ObjectName, PythonCode, SceneInfo, StatusString


class BlenderPort(ABC):
    """Port interface for low-level Blender operations via socket connection."""

    @abstractmethod
    async def execute_code(self, code: PythonCode) -> StatusString:
        """Execute arbitrary Python code in Blender and return result."""
        pass

    @abstractmethod
    async def get_scene_info(self) -> SceneInfo:
        """Retrieve current scene information."""
        pass

    @abstractmethod
    async def get_object_info(self, name: ObjectName) -> BlenderObject | None:
        """Get information about a specific object by name."""
        pass

    @abstractmethod
    async def get_screenshot(self, max_size: MaxSize | None = None) -> ImageBytes:
        """Capture viewport screenshot as PNG bytes."""
        pass
