"""
Infrastructure: Adapter for Tencent Hunyuan3D AI 3D Generation.
"""

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
    ProviderError,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer")


class HunyuanGenerationAdapter(GenerationProviderPort):
    """Implementation of GenerationProviderPort for Tencent Hunyuan3D."""

    def __init__(self, connection: BlenderConnectionPort):
        self.provider_name = "Hunyuan3D"
        self._connection = connection

    def _get_conn(self) -> BlenderConnectionPort:
        return self._connection

    async def generate_from_text(self, prompt: str) -> str:
        try:
            conn = self._get_conn()
            result = conn.send_command(
                ActionName("create_hunyuan_job"),
                {
                    "text_prompt": prompt,
                    "image": None,
                },
            )
            if "JobId" in result.get("Response", {}):
                job_id = result["Response"]["JobId"]
                return f"job_{job_id}"
            else:
                raise ProviderError(ErrorMessage(f"Hunyuan3D generation failed: {result}"))
        except Exception as e:
            logger.error(f"Hunyuan3D generation error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e

    async def get_job_status(self, job_id: str) -> JobStatus:
        try:
            conn = self._get_conn()
            # job_id is usually "job_xxx", we might need to strip "job_"
            internal_job_id = job_id.replace("job_", "")
            result = conn.send_command(ActionName("poll_hunyuan_job_status"), {"job_id": internal_job_id})

            # Map Hunyuan status to Domain JobStatus
            # "DONE" -> COMPLETED
            # "RUN" -> RUNNING
            # Others -> FAILED
            hunyuan_status = result.get("Status")
            status_str = "PENDING"
            if hunyuan_status == "DONE":
                status_str = "COMPLETED"
            elif hunyuan_status == "RUN":
                status_str = "RUNNING"
            else:
                status_str = "FAILED"

            return JobStatus(
                job_id=JobId(job_id),
                status=JobState(status_str),
                progress=Progress(1.0)
                if status_str == "COMPLETED"
                else Progress(0.5)
                if status_str == "RUNNING"
                else Progress(0.0),
                result_url=result.get("ResultFile3Ds") if status_str == "COMPLETED" else None,
            )
        except Exception as e:
            logger.error(f"Hunyuan3D status error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e

    # ─── GenerationProviderPort abstract implementations ──────────────────────

    async def start_generation(self, request: GenerationStartRequestVO) -> GenerationStartResponseVO:
        """Start generation via Hunyuan. Delegates to existing generate_from_text."""
        job_id = await self.generate_from_text(request.prompt or "")
        return GenerationStartResponseVO(job_id=JobId(job_id), status=JobState("started"))

    async def poll_generation(self, request: GenerationStatusRequestVO) -> GenerationStatusResponseVO:
        """Poll Hunyuan job status. Delegates to existing get_job_status."""
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
