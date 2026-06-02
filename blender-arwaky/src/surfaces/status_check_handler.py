"""MCP Job Management for BlenderMCP — delegates to AgentOrchestrator via DI (AES compliant)."""

from contract import AgentDiContainerAggregate
from taxonomy import JobId, Prompt, ProviderName


class StatusCheckHandler:
    """Handler for checking generation job status."""

    _contract_ref: AgentDiContainerAggregate

    @staticmethod
    def register_check_status(mcp):
        @mcp.tool()
        async def check_status(job_id: JobId, provider: ProviderName | None = None) -> Prompt:
            """
            Check the status of a long-running generation task via agent layer.

            Args:
                job_id: The ID of the job to check (request_id, task_uuid, or job_id)
                provider: The provider type (rodin, hunyuan, auto)
            """
            from agent.agent_di_container import get_container

            resolved_provider = provider or ProviderName("auto")
            container: AgentDiContainerAggregate = get_container()
            orchestrator = container.core_agent_orchestrator
            prov_str = str(resolved_provider).lower()
            if prov_str == "auto":
                prov_str = "hunyuan" if "hunyuan" in str(job_id).lower() else "hyper3d"

            return await orchestrator.check_status(ProviderName(prov_str), JobId(str(job_id)))


# Module-level alias for backward compatibility
register_check_status = StatusCheckHandler.register_check_status
