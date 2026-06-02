"""
MCP Command Catalog for BlenderMCP - DDD Compliant Version

Re-exports the canonical COMMAND_CATALOG from taxonomy.
All command definitions live in taxonomy; this surface handler provides
query helpers and backward-compatible registration.

AES Compliance:
- Pure query logic only; no business rules
- No imports from capabilities/infrastructure/agent
- All data sourced from taxonomy
"""

# Import canonical catalog from taxonomy (single source of truth)
from contract import CommandCatalogPort
from taxonomy import CapabilityRef, DomainRef, Prompt, StringList
from taxonomy.blender_command_vo import CommandCatalog


class CommandCatalogSurfaceHandler:
    """Surface handler for command catalog operations."""

    _contract_ref: CommandCatalogPort
    """Handler for command catalog queries and MCP registration."""

    @staticmethod
    def list_commands(domain: DomainRef | None = None) -> StringList:
        domain = domain or DomainRef("all")
        """List available action names, optionally filtered by domain."""
        if domain == "all":
            return StringList(CommandCatalog.list_actions())
        return StringList(
            [name for name, spec in CommandCatalog.COMMAND_CATALOG.items() if spec.get("domain") == domain]
        )

    @staticmethod
    def filter_by_domain(domain: DomainRef):
        """Return command specs filtered by domain."""
        return {k: v for k, v in CommandCatalog.COMMAND_CATALOG.items() if v.get("domain") == domain}

    @staticmethod
    def get_actions_by_capability(capability_ref: CapabilityRef) -> StringList:
        """Return action names mapped to a given capability reference."""
        return StringList(
            [name for name, spec in CommandCatalog.COMMAND_CATALOG.items() if spec.get("capability") == capability_ref]
        )

    @staticmethod
    def register_command_catalog(mcp):
        """
        Register MCP tools for command discovery.

        Note: This is a legacy shim. New code should use tools_registry_surface instead.
        """
        import json

        @mcp.tool()
        async def list_commands_tool(domain: DomainRef | None = None) -> Prompt:
            """List all available actions in BlenderMCP."""
            domain = domain or DomainRef("all")
            filtered = CommandCatalogSurfaceHandler.list_commands(domain)
            return Prompt(json.dumps(filtered, indent=2))

        return list_commands_tool


# Module-level aliases for backward compatibility
list_commands = CommandCatalogSurfaceHandler.list_commands
filter_by_domain = CommandCatalogSurfaceHandler.filter_by_domain
get_actions_by_capability = CommandCatalogSurfaceHandler.get_actions_by_capability
register_command_catalog = CommandCatalogSurfaceHandler.register_command_catalog
