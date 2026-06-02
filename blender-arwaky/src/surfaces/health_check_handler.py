"""Health Check for BlenderMCP — delegates directly to Agent container aggregate (AES compliant)."""

from contract import AgentDiContainerAggregate
from taxonomy import Prompt


class HealthCheckHandler:
    """Handler for health check operations."""

    _contract_ref: AgentDiContainerAggregate

    @staticmethod
    def register_health_check(mcp):
        @mcp.tool()
        async def health_check() -> Prompt:
            """Check the health and connectivity of BlenderMCP via Agent aggregate."""
            from agent.agent_di_container import get_container

            container: AgentDiContainerAggregate = get_container()
            orchestrator = container.core_agent_orchestrator
            return orchestrator.health_check()


# Module-level alias for backward compatibility
register_health_check = HealthCheckHandler.register_health_check
