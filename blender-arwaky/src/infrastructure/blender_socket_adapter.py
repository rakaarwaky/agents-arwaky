"""
Infrastructure: Adapter for Blender Socket Connection.
"""

import logging
import os
import tempfile

from contract import BlenderConnectionPort, BlenderPort
from taxonomy import (
    ActionName,
    BlenderObject,
    ConnectionError,
    ErrorMessage,
    ExecutionError,
    ImageBytes,
    MaxSize,
    ObjectName,
    PythonCode,
    SceneInfo,
    StatusString,
)

logger = logging.getLogger("BlenderMCPServer")


class BlenderSocketAdapter(BlenderPort):
    """Implementation of BlenderPort using a persistent socket connection."""

    def __init__(self, connection_port: BlenderConnectionPort):
        self._connection = connection_port

    def _get_conn(self) -> BlenderConnectionPort:
        """Internal helper for connection access."""
        if not self._connection:
            raise ConnectionError(ErrorMessage("Blender connection not initialized"))
        return self._connection

    async def execute_code(self, code: PythonCode) -> StatusString:
        try:
            conn = self._get_conn()
            result = conn.send_command(ActionName("execute_code"), {"code": str(code)})
            return StatusString(result.get("result", ""))
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            raise ExecutionError(ErrorMessage(str(e))) from e

    async def get_scene_info(self) -> SceneInfo:
        try:
            conn = self._get_conn()
            result = conn.send_command(ActionName("get_scene_info"))
            # Map the dict to SceneInfo model
            return SceneInfo(**result)
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Error getting tool_scene_ops info: {str(e)}")
            raise ExecutionError(ErrorMessage(str(e))) from e

    async def get_object_info(self, name: ObjectName) -> BlenderObject | None:
        try:
            conn = self._get_conn()
            result = conn.send_command(ActionName("get_object_info"), {"name": str(name)})
            if not result:
                return None
            return BlenderObject(**result)
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Error getting object info: {str(e)}")
            return None

    async def get_screenshot(self, max_size: MaxSize | None = None) -> ImageBytes:
        max_size = max_size or MaxSize(800)
        try:
            conn = self._get_conn()
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}.png")
            result = conn.send_command(
                ActionName("get_viewport_screenshot"),
                {"max_size": int(max_size), "filepath": temp_path, "format": "png"},
            )
            if isinstance(result, dict) and "error" in result:
                raise ExecutionError(ErrorMessage(result["error"]))
            if not os.path.exists(temp_path):
                raise ExecutionError(ErrorMessage("Screenshot file was not created by Blender"))
            with open(temp_path, "rb") as f:
                image_bytes = f.read()
            os.remove(temp_path)
            return ImageBytes(image_bytes)
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Error getting screenshot: {str(e)}")
            raise ExecutionError(ErrorMessage(str(e))) from e
