"""
Contract: Render Operations Contract (ABC based).
"""

from abc import ABC, abstractmethod

from taxonomy import (
    CoordinateList,
    GetScreenshotRequestVO,
    Prompt,
    RenderEngine,
    RenderRequestVO,
    RenderResponseVO,
    RenderSamples,
    RotationVector,
    RuleName,
    ScreenshotResponseVO,
    UseDenoising,
)


class RenderOperateProtocol(ABC):
    """Interface for rendering, viewport capture, and camera setup."""

    @abstractmethod
    async def get_viewport_screenshot(self, request: GetScreenshotRequestVO) -> ScreenshotResponseVO:
        """Capture active 3D viewport."""
        pass

    @abstractmethod
    async def setup_camera(
        self, location: CoordinateList, rotation: RotationVector, target: CoordinateList | None = None
    ) -> Prompt:
        """Initialize and position camera."""
        pass

    @abstractmethod
    async def setup_render(
        self,
        engine: RenderEngine | None = None,
        samples: RenderSamples | None = None,
        resolution: CoordinateList | None = None,
        use_denoising: UseDenoising | None = None,
    ) -> Prompt:
        """Configure render engine settings."""
        pass

    @abstractmethod
    async def apply_composition(self, rule: RuleName | None = None) -> Prompt:
        """Apply compositional guides to active camera."""
        pass

    @abstractmethod
    async def render(self, request: RenderRequestVO) -> RenderResponseVO:
        """Execute full frame render to file."""
        pass
