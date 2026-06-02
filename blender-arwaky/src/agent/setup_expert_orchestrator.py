"""
SceneExpert: Handles tool_scene_ops composition, camera setup, rendering, and environment.
"""

import logging

from contract import RenderOperateProtocol, SceneOperateProtocol, SetupExpertOrchestratorAggregate
from taxonomy import (
    CleanupSceneRequestVO,
    CoordinateList,
    GetSceneInfoRequestVO,
    HdriId,
    ObjectName,
    RenderEngine,
    RenderSamples,
    RotationVector,
    RuleName,
    SceneInfo,
    SetupEnvironmentRequestVO,
    StatusString,
)

from .agent_logic_coordinator import ExpertOrchestratorLogic

logger = logging.getLogger("BlenderMCPServer.Agents")


class SetupExpertOrchestrator(ExpertOrchestratorLogic, SetupExpertOrchestratorAggregate):
    """Specialist for all things scene-related."""

    _contract_name: StatusString = StatusString("SetupExpertOrchestrator")
    _scene_ref: SceneInfo
    _obj_ref: ObjectName = ObjectName("ref")

    def __init__(self, blender_mgr: SceneOperateProtocol, render_mgr: RenderOperateProtocol | None = None):
        super().__init__("SetupExpertOrchestrator")
        self.blender = blender_mgr
        self.render = render_mgr

    async def execute(self, action: str, params: dict[str, object] | None = None) -> dict[str, object]:
        if params is None:
            params = {}

        self.log_info(f"Action: {action}, params: {params}")

        try:
            if action == "cleanup":
                return await self._execute_cleanup()
            elif action == "info":
                return await self._execute_info()
            elif action == "setup_camera":
                return await self._execute_setup_camera(params)
            elif action == "setup_render":
                return await self._execute_setup_render(params)
            elif action == "compose":
                return await self._execute_compose(params)
            elif action == "setup_environment":
                return await self._execute_setup_environment(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            self.log_error(f"SceneExpert failed: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_cleanup(self) -> dict[str, object]:
        await self.blender.cleanup_scene(CleanupSceneRequestVO())
        return {"success": True, "message": "Scene cleaned"}

    async def _execute_info(self) -> dict[str, object]:
        scene_data = await self.blender.get_scene_info(GetSceneInfoRequestVO())
        return {"success": True, "tool_scene_ops": scene_data}

    async def _execute_setup_camera(self, params: dict[str, object]) -> dict[str, object]:
        if self.render is None:
            return {"success": False, "error": "Render manager not injected"}
        location_val = params.get("location")
        location = CoordinateList(location_val) if isinstance(location_val, list) else CoordinateList([0.0, -5.0, 2.0])
        rotation_val = params.get("rotation")
        rotation = RotationVector(rotation_val) if isinstance(rotation_val, list) else RotationVector([1.0, 0.0, 0.0])
        target_val = params.get("target")
        target = CoordinateList(target_val) if isinstance(target_val, list) else None
        await self.render.setup_camera(location, rotation, target)
        return {"success": True, "message": "Camera configured"}

    async def _execute_setup_render(self, params: dict[str, object]) -> dict[str, object]:
        if self.render is None:
            return {"success": False, "error": "Render manager not injected"}
        engine = RenderEngine(str(params.get("engine", "CYCLES")))
        samples_val = params.get("samples", 128)
        samples = RenderSamples(int(samples_val) if isinstance(samples_val, (int, str)) else 128)
        res_val = params.get("resolution")
        resolution = CoordinateList(res_val) if isinstance(res_val, list) else None
        await self.render.setup_render(engine, samples, resolution)
        return {"success": True, "message": f"Render set to {engine}, {samples} samples"}

    async def _execute_compose(self, params: dict[str, object]) -> dict[str, object]:
        if self.render is None:
            return {"success": False, "error": "Render manager not injected"}
        rule = RuleName(str(params.get("rule", "thirds")))
        await self.render.apply_composition(rule)
        return {"success": True, "message": f"Composition rule '{rule}' applied"}

    async def _execute_setup_environment(self, params: dict[str, object]) -> dict[str, object]:
        hdri = params.get("hdri_name", "default_studio")
        await self.blender.setup_environment(SetupEnvironmentRequestVO(hdri_id=HdriId(str(hdri))))
        return {"success": True, "message": f"Environment set to '{hdri}'"}
