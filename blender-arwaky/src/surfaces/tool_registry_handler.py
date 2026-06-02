"""
MCP Tools Registry — Registers exactly 5 MCP tools (AES handler layer).

Tool list (unlimited CLI via single entry point):
  1. execute_command  — Universal action executor (dispatches to CLI)
  2. list_commands    — Command catalog discovery
  3. read_skill_context — SKILL.md documentation reader
  4. check_status     — Job status monitoring (generation/import/render)
  5. health_check     — System health diagnostics

All tools delegate to the agent layer; handlers never call capabilities directly.
"""

from contract import CommandCatalogPort


class ToolRegistryHandler:
    """Handler for tool registry ."""

    _contract_ref: CommandCatalogPort
    """Registry for all MCP tools. Handlers never call capabilities directly."""

    @staticmethod
    def register_tools(mcp):
        """
        Register the 5 core MCP tools for BlenderMCP.
        """
        from .command_execute_handler import register_execute_command
        from .commands_list_handler import register_list_commands
        from .health_check_handler import register_health_check
        from .skill_read_handler import register_read_skill_context
        from .status_check_handler import register_check_status

        # Tool 1: Universal executor
        register_execute_command(mcp)

        # Tool 2: Command discovery
        register_list_commands(mcp)

        # Tool 3: Documentation reader
        register_read_skill_context(mcp)

        # Tool 4: Job status
        register_check_status(mcp)

        # Tool 5: Health check
        register_health_check(mcp)


# Module-level alias for backward compatibility
register_tools = ToolRegistryHandler.register_tools
