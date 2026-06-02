"""
Contract: Scene Operations Contract (ABC based).
"""

from abc import ABC, abstractmethod

from taxonomy import (
    CleanupSceneRequestVO,
    CleanupSceneResponseVO,
    GetSceneInfoRequestVO,
    GetSceneInfoResponseVO,
    SetupEnvironmentRequestVO,
    SetupEnvironmentResponseVO,
)

from .adapter_blender_port import BlenderPort


class SceneOperateProtocol(ABC):
    """Interface for scene-level management (cleanup, environment, metadata)."""

    @property
    @abstractmethod
    def blender(self) -> BlenderPort:
        """Access the low-level Blender port."""
        pass

    @abstractmethod
    async def cleanup_scene(self, request: CleanupSceneRequestVO) -> CleanupSceneResponseVO:
        """Remove objects and reset scene state."""
        pass

    @abstractmethod
    async def setup_environment(self, request: SetupEnvironmentRequestVO) -> SetupEnvironmentResponseVO:
        """Set HDRI and world environment properties."""
        pass

    @abstractmethod
    async def get_scene_info(self, request: GetSceneInfoRequestVO) -> GetSceneInfoResponseVO:
        """Retrieve current scene metadata and object tree."""
        pass
