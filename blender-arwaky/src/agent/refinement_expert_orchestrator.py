"""
RefinementExpert: Iterative tool_scene_ops improvement via autonomous feedback loop.
"""

import asyncio
import logging
from typing import Any

from contract import ExpertBaseOrchestratorAggregate, RefinementExpertOrchestratorAggregate
from taxonomy import ObjectName, StatusString, SuccessFlag

from .agent_logic_coordinator import ExpertOrchestratorLogic

logger = logging.getLogger("BlenderMCPServer.Agents")


class RefinementExpertOrchestrator(ExpertOrchestratorLogic, RefinementExpertOrchestratorAggregate):
    """
    Autonomous refinement engine - iteratively improves the tool_scene_ops.
    """

    _contract_name: StatusString = StatusString("RefinementExpertOrchestrator")
    _success_ref: SuccessFlag = SuccessFlag(True)
    _obj_ref: ObjectName = ObjectName("ref")

    def __init__(
        self,
        setup_scene_expert: ExpertBaseOrchestratorAggregate,
        search_asset_expert: ExpertBaseOrchestratorAggregate,
        generate_ai_expert: ExpertBaseOrchestratorAggregate,
    ):
        super().__init__("RefinementExpertOrchestrator")
        self.tool_scene_ops = setup_scene_expert
        self.asset = search_asset_expert
        self.generation = generate_ai_expert

    async def execute(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if params is None:
            params = {}

        self.log_info(f"Action: {action}, params: {params}")

        if action == "refine_loop":
            objective = params.get("objective", "")
            max_iterations = params.get("max_iterations", 5)
            return await self._run_refinement_loop(objective, max_iterations)

        elif action == "analyze_gaps":
            scene_info = await self.tool_scene_ops.execute("info", {})
            return {
                "success": True,
                "analysis": {
                    "object_count": len(scene_info.get("tool_scene_ops", {}).get("objects", [])),
                    "needs": ["more objects", "better lighting"],
                },
            }

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _run_refinement_loop(self, objective: str, max_iterations: int) -> dict[str, Any]:
        self.log_info(f"Starting refinement loop. Objective: {objective}")
        steps = []

        for iteration in range(1, max_iterations + 1):
            self.log_info(f"Iteration {iteration}/{max_iterations}")
            step_log: dict[str, Any] = {"iteration": iteration, "actions": []}

            # Query tool_scene_ops via SceneExpert
            scene_info = await self.tool_scene_ops.execute("info", {})
            obj_count = len(scene_info.get("tool_scene_ops", {}).get("objects", []))
            step_log["object_count"] = obj_count

            if obj_count == 0:
                asset_result = await self.asset.execute("generate_if_missing", {"query": objective})
                step_log["actions"].append(("generate_if_missing", asset_result))
                await asyncio.sleep(2)

            # Lighting
            light_result = await self.tool_scene_ops.execute("setup_environment", {"hdri_name": "default_studio"})
            step_log["actions"].append(("lighting", light_result))

            # Camera
            cam_result = await self.tool_scene_ops.execute(
                "setup_camera",
                {"location": [0, -5, 2], "rotation": [1.0, 0, 0], "target": [0, 0, 0]},
            )
            step_log["actions"].append(("camera", cam_result))

            steps.append(step_log)

            if obj_count >= 2:
                self.log_info("Convergence criteria met (object count >= 2). Stopping.")
                break

        return {
            "success": True,
            "iterations": len(steps),
            "steps": steps,
            "objective": objective,
            "message": f"Refinement complete after {len(steps)} iterations",
        }
