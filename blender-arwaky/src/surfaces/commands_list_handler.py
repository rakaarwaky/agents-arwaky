"""
MCP Tool 2: list_commands — Returns the command catalog (discovery).

Lists all available actions, their parameters, descriptions, and domains.
Surface delegates to Agent container via its aggregate contract (AES compliant).
"""

from contract import AgentDiContainerAggregate
from taxonomy import DomainRef, FormatRef, Prompt


class CommandsListHandler:
    """Handler for listing available MCP commands via agent container."""

    @staticmethod
    def register_list_commands(mcp):
        """Register the list_commands tool (MCP Tool #2)."""

        @mcp.tool()
        def list_commands(
            domain: DomainRef | None = None,
            format: FormatRef | None = None,
        ) -> Prompt:
            """
            List all available BlenderMCP actions.

            Args:
                domain: Filter by domain (scene, object, viewport, render, io, infrastructure, asset, generation). Omit to list all.
                format: Output format — 'detailed' (full spec per action) or 'summary' (names + descriptions only)

            Returns:
                JSON string with command catalog
            """
            # Don't coerce None→DomainRef("") — that causes filter_by_domain("")
            # to match zero commands and return {}.
            resolved_format = format or FormatRef("detailed")

            from agent.agent_di_container import get_container

            container: AgentDiContainerAggregate = get_container()
            orchestrator = container.core_agent_orchestrator
            return orchestrator.list_commands(domain, resolved_format)


# Module-level alias for backward compatibility
register_list_commands = CommandsListHandler.register_list_commands
