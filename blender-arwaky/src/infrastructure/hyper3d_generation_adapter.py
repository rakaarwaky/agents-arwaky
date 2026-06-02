import json
import logging

from contract import (
    BlenderConnectionPort,
    GenerationProviderPort,
)
from taxonomy import (
    ActionName,
    ErrorMessage,
    GenerationStartRequestVO,
    GenerationStartResponseVO,
    GenerationStatusRequestVO,
    GenerationStatusResponseVO,
    ImportGeneratedAssetRequestVO,
    ImportGeneratedAssetResponseVO,
    JobId,
    JobState,
    JobStatus,
    ObjectName,
    Progress,
    Prompt,
    ProviderError,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer")


class Hyper3DGenerationAdapter(GenerationProviderPort):
    """Implementation of GenerationProviderPort for Hyper3D Rodin."""

    def __init__(self, connection_port: BlenderConnectionPort):
        self.provider_name = "Hyper3D"
        self._connection = connection_port

    def _get_conn(self) -> BlenderConnectionPort:
        return self._connection

    async def generate_from_text(self, prompt: Prompt) -> JobId:
        try:
            conn = self._get_conn()
            result = conn.send_command(
                ActionName("create_rodin_job"),
                {
                    "text_prompt": str(prompt),
                    "images": None,
                    "bbox_condition": None,
                },
            )

            if result.get("request_id"):  # FAL_AI
                return JobId(result["request_id"])
            elif result.get("submit_time"):  # MAIN_SITE
                return JobId(
                    json.dumps({"task_uuid": result["uuid"], "subscription_key": result["jobs"]["subscription_key"]})
                )
            else:
                raise ProviderError(ErrorMessage(f"Hyper3D generation failed: {result}"))
        except Exception as e:
            logger.error(f"Hyper3D generation error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e

    @staticmethod
    def _parse_job_id_kwargs(job_id: JobId) -> dict:
        """Parse job_id (possibly JSON-packed) into kwargs dict for polling."""
        kwargs = {}
        try:
            data = json.loads(str(job_id))
            if isinstance(data, dict):
                if "subscription_key" in data:
                    kwargs["subscription_key"] = data["subscription_key"]
                if "request_id" in data:
                    kwargs["request_id"] = data["request_id"]  # pragma: no cover
            else:
                kwargs["request_id"] = str(job_id)
        except json.JSONDecodeError:
            kwargs["request_id"] = str(job_id)
        return kwargs

    @staticmethod
    def _map_status_result_to_status(result) -> str:
        """Map the Hyper3D poll result to a status string (COMPLETED/FAILED/RUNNING/PENDING)."""
        if isinstance(result, list):
            if all(s == "Done" for s in result):
                return "COMPLETED"
            elif any(s == "Failed" for s in result):
                return "FAILED"
            else:
                return "RUNNING"
        elif isinstance(result, dict):
            fal_status = result.get("status")
            if fal_status == "COMPLETED":
                return "COMPLETED"
            elif fal_status in ["IN_PROGRESS", "IN_QUEUE"]:
                return "RUNNING"
            else:
                return "FAILED"
        return "PENDING"

    @staticmethod
    def _build_job_status(job_id: JobId, status_str: str) -> JobStatus:
        """Build a JobStatus instance with appropriate progress."""
        if status_str == "COMPLETED":
            progress = Progress(1.0)
        elif status_str == "RUNNING":
            progress = Progress(0.5)
        else:
            progress = Progress(0.0)
        return JobStatus(
            job_id=job_id,
            status=JobState(status_str),
            progress=progress,
        )

    async def get_job_status(self, job_id: JobId) -> JobStatus:
        try:
            conn = self._get_conn()
            kwargs = self._parse_job_id_kwargs(job_id)
            result = conn.send_command(ActionName("poll_rodin_job_status"), kwargs)
            status_str = self._map_status_result_to_status(result)
            return self._build_job_status(job_id, status_str)
        except Exception as e:
            logger.error(f"Hyper3D status error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e

    # ─── GenerationProviderPort abstract implementations ──────────────────────

    async def start_generation(self, request: GenerationStartRequestVO) -> GenerationStartResponseVO:
        """Start generation via Hyper3D. Delegates to existing generate_from_text."""
        job_id = await self.generate_from_text(request.prompt)
        return GenerationStartResponseVO(job_id=job_id, status=JobState("started"))

    async def poll_generation(self, request: GenerationStatusRequestVO) -> GenerationStatusResponseVO:
        """Poll Hyper3D job status. Delegates to existing get_job_status."""
        status = await self.get_job_status(request.job_id)
        return GenerationStatusResponseVO(
            job_id=status.job_id,
            status=status.status,
            progress=status.progress,
            error=status.error,
        )

    async def import_generated_asset(self, request: ImportGeneratedAssetRequestVO) -> ImportGeneratedAssetResponseVO:
        """Import generated asset into Blender."""
        conn = self._get_conn()
        result = conn.send_command(
            ActionName("import_generated"),
            {
                "job_id": str(request.asset_id),
            },
        )
        return ImportGeneratedAssetResponseVO(
            success=SuccessFlag(result.get("success", False)),
            object_name=ObjectName(result.get("object_name", "")),
            blender_id=ObjectName(result.get("blender_id", "") or result.get("object_name", "")),
            message=ErrorMessage(result.get("message", "Import complete") or ""),
        )
