"""
Contract: Port interface for viewport screenshot capture.

Defines the contract for capturing the Blender 3D viewport as an image.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import MaxImageSize


class ViewportCapturePort(ABC):
    """Port interface for capturing viewport screenshots from Blender."""

    @abstractmethod
    def get_viewport_screenshot(self, max_size: MaxImageSize | None = None) -> bytes:
        """Capture a screenshot of the current Blender 3D viewport. Returns PNG bytes."""
        pass
