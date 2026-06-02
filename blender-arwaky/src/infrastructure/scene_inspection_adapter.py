import json
import logging

from contract import BlenderConnectionPort, CodeExecutionPort, SceneInspectionPort
from taxonomy import ActionName, BlenderObject, BlenderObjectList, ObjectName, ObjectType, Prompt, SceneInfo, Vector3D

logger = logging.getLogger("BlenderMCPServer")


class SceneInspectionAdapter(SceneInspectionPort):
    """Wrapper class for scene inspection functions."""

    _scene_entity_ref: SceneInfo = SceneInfo(objects=BlenderObjectList([]))
    _object_entity_ref: BlenderObject = BlenderObject(
        name=ObjectName("ref"),
        type=ObjectType("MESH"),
        location=Vector3D(0.0, 0.0, 0.0),
        rotation=Vector3D(0.0, 0.0, 0.0),
        scale=Vector3D(1.0, 1.0, 1.0),
    )

    def __init__(self, connection_port: BlenderConnectionPort, execution_port: CodeExecutionPort):
        self._connection_port = connection_port
        self._execution_port = execution_port

    async def get_scene_info(self) -> Prompt:
        """Get detailed information about the current Blender scene."""
        try:
            result = self._connection_port.send_command(ActionName("get_scene_info"))
            return Prompt(json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error getting scene info from Blender: {str(e)}")
            return Prompt(f"Error getting scene info: {str(e)}")

    async def get_object_info(self, object_name: ObjectName) -> Prompt:
        """Get detailed info about a specific object in the scene."""
        try:
            result = self._connection_port.send_command(ActionName("get_object_info"), {"name": object_name})
            return Prompt(json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error getting object info from Blender: {str(e)}")
            return Prompt(f"Error getting object info: {str(e)}")

    async def cleanup_scene(self) -> Prompt:
        """Remove all objects from the scene."""
        code = "import bpy\nbpy.ops.object.select_all(action='SELECT')\nbpy.ops.object.delete()\n"
        try:
            result = await self._execution_port.execute_blender_code(Prompt(code))
            return result
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return Prompt(f"Error cleaning scene: {e}")
