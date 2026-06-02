import logging
import os
import tempfile

from contract import BlenderConnectionPort, ViewportCapturePort
from taxonomy import ActionName, BoundingBox, MaxImageSize, Vector3D

logger = logging.getLogger("BlenderMCPServer")


class ViewportCaptureAdapter(ViewportCapturePort):
    """Wrapper class for viewport capture functions."""

    _bbox_ref: BoundingBox = BoundingBox(Vector3D(0.0, 0.0, 0.0), Vector3D(0.0, 0.0, 0.0))

    def __init__(self, connection_port: BlenderConnectionPort):
        self._connection_port = connection_port

    def get_viewport_screenshot(self, max_size: MaxImageSize | None = None) -> bytes:
        """
        Capture a screenshot of the current Blender 3D viewport.

        Parameters:
        - max_size: Maximum size in pixels for the largest dimension (default: 800)

        Returns the screenshot as image bytes.
        """
        try:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}.png")

            result = self._connection_port.send_command(
                ActionName("get_viewport_screenshot"), {"max_size": max_size, "filepath": temp_path, "format": "png"}
            )

            if not result:
                raise RuntimeError("No result returned from Blender")

            if not os.path.exists(temp_path):
                raise RuntimeError(f"Screenshot file was not created at {temp_path}")

            with open(temp_path, "rb") as f:
                image_bytes = f.read()

            os.remove(temp_path)
            return image_bytes
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            raise Exception(f"Screenshot failed: {str(e)}") from e
