"""
GenerationExpert: Manages AI-powered 3D asset generation workflows.
Handles Hyper3D and Hunyuan, with polling and auto-import.
"""

import asyncio
import logging
from typing import Any

from contract import GenerationExpertOrchestratorAggregate, GenerationProtocol, SceneOperateProtocol
from taxonomy import JobId, JobState, Prompt, StatusString

from .agent_logic_coordinator import ExpertOrchestratorLogic

logger = logging.getLogger("BlenderMCPServer.Agents")


class GenerationExpertOrchestrator(ExpertOrchestratorLogic, GenerationExpertOrchestratorAggregate):
    _contract_name: StatusString = StatusString("GenerationExpertOrchestrator")
    _job_id_ref: JobId = JobId("ref")
    _job_state_ref: JobState = JobState("completed")
    _prompt_ref: Prompt = Prompt("ref")
    """
    Specialist for AI generation:
    - Start generation jobs (Hyper3D/Hunyuan)
    - Poll until completion
    - Auto-import generated assets
    - Retry logic and error handling
    """

    def __init__(self, gen_mgr: GenerationProtocol, blender_mgr: SceneOperateProtocol):
        super().__init__("GenerationExpertOrchestrator")
        self.gen_mgr = gen_mgr
        self.blender = blender_mgr

    async def execute(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if params is None:
            params = {}

        self.log_info(f"Action: {action}, params: {params}")

        try:
            if action == "generate":
                return await self._handle_generate(params)
            elif action == "poll":
                return await self._handle_poll(params)
            elif action == "generate_and_import":
                return await self._handle_generate_and_import(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            self.log_error(f"GenerationExpert failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_generate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Start a generation job."""
        provider = params.get("provider", "tool_generate_hyper3d")
        prompt = params.get("prompt", "")
        if not prompt:
            return {"success": False, "error": "prompt required"}

        job_id = await self.gen_mgr.start_generation(provider, prompt)
        self.log_info(f"Started {provider} job: {job_id}")
        return {
            "success": True,
            "job_id": job_id,
            "provider": provider,
            "message": f"Generation started with {provider}",
        }

    async def _handle_poll(self, params: dict[str, Any]) -> dict[str, Any]:
        """Poll a generation job for status."""
        provider = params.get("provider", "")
        job_id = params.get("job_id", "")
        if not provider or not job_id:
            return {"success": False, "error": "provider and job_id required"}

        status = await self.gen_mgr.check_status(provider, job_id)
        return {
            "success": True,
            "provider": provider,
            "job_id": job_id,
            "status": status.status,
            "result_url": status.result_url,
        }

    async def _handle_generate_and_import(self, params: dict[str, Any]) -> dict[str, Any]:
        """One-shot: generate, wait, import."""
        provider = params.get("provider", "tool_generate_hyper3d")
        prompt = params.get("prompt", "")
        max_wait = params.get("max_wait_seconds", 120)
        poll_interval = params.get("poll_interval", 3)

        if not prompt:
            return {"success": False, "error": "prompt required"}

        # Start generation
        job_id = await self.gen_mgr.start_generation(provider, prompt)
        self.log_info(f"Started {provider} job: {job_id}")

        # Poll until complete
        import time

        start_time = time.time()
        while True:
            if time.time() - start_time > max_wait:
                return {"success": False, "error": "Timeout waiting for generation"}

            status = await self.gen_mgr.check_status(provider, job_id)
            if status.status == "COMPLETED":
                break
            elif status.status == "FAILED":
                return {"success": False, "error": status.error or "Generation failed"}
            await asyncio.sleep(poll_interval)  # pragma: no cover

        # Generation completed
        return {
            "success": True,
            "job_id": job_id,
            "provider": provider,
            "result_url": status.result_url,
            "message": "Generation completed",
        }
