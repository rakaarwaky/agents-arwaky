"""Handler: Scene-level management operations."""

import logging

from contract import (
    BlenderPort,
    SceneOperateProtocol,
)
from taxonomy import (
    BlenderMCPError,
    CleanupSceneRequestVO,
    CleanupSceneResponseVO,
    ErrorMessage,
    GetSceneInfoRequestVO,
    GetSceneInfoResponseVO,
    ObjectCount,
    PythonCode,
    SetupEnvironmentRequestVO,
    SetupEnvironmentResponseVO,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer")


class SceneOperateExecutor(SceneOperateProtocol):
    """Business logic for scene management (cleanup, environment, info)."""

    def __init__(self, blender_port: BlenderPort):
        self._blender = blender_port

    @property
    def blender(self) -> BlenderPort:
        return self._blender

    async def cleanup_scene(self, _request: CleanupSceneRequestVO) -> CleanupSceneResponseVO:
        logger.info("Cleaning up scene...")
        code = "import bpy\nbpy.ops.object.select_all(action='SELECT')\nbpy.ops.object.delete()\n"
        try:
            await self.blender.execute_code(PythonCode(code))
            return CleanupSceneResponseVO(
                success=SuccessFlag(True), objects_removed=ObjectCount(0), message="Scene cleaned up successfully"
            )
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return CleanupSceneResponseVO(
                success=SuccessFlag(False), objects_removed=ObjectCount(0), message=f"Cleanup failed: {e}"
            )

    async def setup_environment(self, request: SetupEnvironmentRequestVO) -> SetupEnvironmentResponseVO:
        logger.info(f"Setting up environment with HDRI: {request.hdri_id}")
        code = (
            "import bpy\n"
            "world = bpy.context.scene.world\n"
            "if world is None:\n"
            "    world = bpy.data.worlds.new('World')\n"
            "    bpy.context.scene.world = world\n"
            "world.use_nodes = True\n"
        )
        try:
            await self.blender.execute_code(PythonCode(code))
            return SetupEnvironmentResponseVO(
                success=SuccessFlag(True), hdri_path=None, message="Environment setup successfully"
            )
        except Exception as e:
            return SetupEnvironmentResponseVO(
                success=SuccessFlag(False), hdri_path=None, message=f"Setup environment failed: {e}"
            )

    async def get_scene_info(self, request: GetSceneInfoRequestVO) -> GetSceneInfoResponseVO:
        logger.info(f"Retrieving scene info: {request}")
        try:
            scene_info = await self.blender.get_scene_info()
            return GetSceneInfoResponseVO(
                success=SuccessFlag(True), scene_info=scene_info, message="Scene info retrieved successfully"
            )
        except Exception as e:
            logger.error(f"get_scene_info failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to get scene info: {e}")) from e
