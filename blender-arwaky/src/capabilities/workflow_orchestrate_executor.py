"""
Executor: Complex multi-step workflow orchestration.

This is a capabilities-layer executor that coordinates across
multiple handlers and providers. It depends on other capabilities
but does so via constructor injection with port interfaces.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contract import AssetSearchProtocol, GenerationProtocol, SceneOperateProtocol

from contract import WorkflowProtocol
from taxonomy import (
    BlenderMCPError,
    CleanupSceneRequestVO,
    HdriId,
    Prompt,
    ProviderError,
    ProviderName,
    PythonCode,
    SearchQuery,
    SetupEnvironmentRequestVO,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer")


class WorkflowExecutor(WorkflowProtocol):
    """Orchestrates multiple capabilities to perform high-level tasks."""

    def __init__(
        self,
        blender_executor: "SceneOperateProtocol",
        asset_collector: "AssetSearchProtocol",
        generation_logic: "GenerationProtocol | None" = None,
    ):
        self.blender = blender_executor
        self.assets = asset_collector
        self.generation = generation_logic

    async def create_basic_scene(self, prompt: Prompt) -> SuccessFlag:
        """
        Workflow:
        1. Cleanup tool_scene_ops.
        2. Search for assets matching prompt.
        3. Place the first relevant asset.
        4. Setup a default environment.
        """
        logger.info(f"Creating basic scene for prompt: {prompt}")
        try:
            # 1. Cleanup
            await self.blender.cleanup_scene(CleanupSceneRequestVO())

            # 2. Search Assets
            assets = await self.assets.search_all(SearchQuery(str(prompt)))
            if not assets:
                logger.warning(f"No assets found for prompt: {prompt}")
                return SuccessFlag(False)

            # 3. Place first asset
            logger.info(f"Placing asset: {assets[0].name}")
            place_code = (
                f"import bpy\nfor obj in bpy.context.selected_objects:\n    obj.location = ({0.0}, {0.0}, {0.0})\n"
            )
            await self.blender.blender.execute_code(PythonCode(place_code))

            # 4. Setup environment (default HDRI for now)
            await self.blender.setup_environment(
                SetupEnvironmentRequestVO(
                    hdri_id=HdriId("default_studio"),
                )
            )

            return SuccessFlag(True)
        except BlenderMCPError as e:
            logger.error(f"Workflow failed: {e}")
            return SuccessFlag(False)

    async def generate_and_import_ai_asset(self, provider_name: ProviderName, prompt: Prompt) -> Prompt:
        """
        Workflow:
        1. Start AI generation.
        2. Wait for completion (poll).
        3. Import into Blender.

        Returns JSON string with result wrapped in Prompt.
        """
        if self.generation is None:
            logger.warning("AI generation workflow not available: no GenerationLogic injected")
            import json

            return Prompt(
                json.dumps({"error": "Generation logic not configured", "action": "generate_and_import_ai_asset"})
            )

        logger.info(f"Starting AI generation workflow: provider={provider_name}, prompt='{str(prompt)[:80]}'")
        try:
            # 1. Start generation
            job_id = await self.generation.start_generation(provider_name, prompt)
            logger.info(f"Generation started: job_id={job_id}")

            # 2. Poll up to 30 times (5s interval = 150s max)
            import asyncio

            max_polls = 30
            poll_interval = 5.0
            for attempt in range(max_polls):
                await asyncio.sleep(poll_interval)
                status = await self.generation.check_status(provider_name, job_id)
                logger.info(f"Poll attempt {attempt + 1}/{max_polls}: status={status.status}")
                if str(status.status).upper() in ("DONE", "COMPLETED", "SUCCESS"):
                    break
                if str(status.status).upper() in ("FAILED", "ERROR", "FAIL"):
                    import json

                    return Prompt(
                        json.dumps(
                            {
                                "error": f"Generation failed: {status.status}",
                                "job_id": str(job_id),
                                "provider": str(provider_name),
                            }
                        )
                    )
            else:
                import json

                return Prompt(
                    json.dumps(
                        {
                            "error": "Generation timed out after 150s",
                            "job_id": str(job_id),
                            "provider": str(provider_name),
                        }
                    )
                )

            # 3. Import via Blender
            import_code = f"import bpy; print('Importing {provider_name} asset from job {job_id}')"
            await self.blender.blender.execute_code(PythonCode(import_code))

            import json

            return Prompt(
                json.dumps(
                    {
                        "success": True,
                        "job_id": str(job_id),
                        "provider": str(provider_name),
                        "message": "Asset generated and imported successfully",
                    }
                )
            )

        except ProviderError as e:
            logger.error(f"Provider error in generation workflow: {e}")
            import json

            return Prompt(json.dumps({"error": str(e), "provider": str(provider_name)}))
        except BlenderMCPError as e:
            logger.error(f"Blender error during import: {e}")
            import json

            return Prompt(json.dumps({"error": str(e)}))
        except Exception as e:
            logger.error(f"Generation workflow failed: {e}", exc_info=True)
            import json

            return Prompt(json.dumps({"error": f"Workflow failed: {str(e)}"}))
