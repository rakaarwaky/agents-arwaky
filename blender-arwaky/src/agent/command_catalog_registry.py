"""
Agent: CommandCatalogAdapter — wraps taxonomy CommandCatalog as CommandCatalogPort.

Bridges the static taxonomy catalog into the contract port interface so that
surfaces can access the catalog through the container without knowing about
taxonomy internals or capabilities.
"""

from contract import CommandCatalogPort
from taxonomy import ActionName, DomainRef, FilePath
from taxonomy.blender_command_vo import CommandCatalog, CommandSpec


class CommandCatalogAdapter(CommandCatalogPort):
    """Adapter that exposes taxonomy CommandCatalog through CommandCatalogPort."""

    _contract_name: str = "CommandCatalogAdapter"
    _compliance: FilePath | None = None

    def get_command_spec(self, action: ActionName) -> CommandSpec | None:
        return CommandCatalog.COMMAND_CATALOG.get(str(action))

    def list_actions(self) -> list[ActionName]:
        return [ActionName(k) for k in CommandCatalog.COMMAND_CATALOG]

    def filter_by_domain(self, domain: DomainRef) -> dict[ActionName, CommandSpec]:
        return {ActionName(k): v for k, v in CommandCatalog.COMMAND_CATALOG.items() if v.get("domain") == domain}
