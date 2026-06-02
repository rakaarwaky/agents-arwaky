from contract import CommandCatalogPort
from taxonomy import ActionName, DomainRef
from taxonomy.blender_command_vo import CommandCatalog, CommandSpec


class CommandCatalogClient(CommandCatalogPort):
    """Infrastructure client for querying the domain command catalog."""

    def get_command_spec(self, action: ActionName) -> CommandSpec | None:
        """CommandCatalogPort: retrieve command spec from COMMAND_CATALOG by action name."""
        return CommandCatalog.COMMAND_CATALOG.get(action)

    def list_actions(self) -> list[ActionName]:
        """CommandCatalogPort: return all available action names from the domain catalog."""
        return [ActionName(act) for act in CommandCatalog.list_actions()]

    def filter_by_domain(self, domain: DomainRef) -> dict[ActionName, CommandSpec]:
        """CommandCatalogPort: return command specs filtered by domain."""
        return {ActionName(k): v for k, v in CommandCatalog.COMMAND_CATALOG.items() if v.get("domain") == domain}


# Helper aliases using a private client instance to preserve static helper behavior
_client_instance = CommandCatalogClient()


def get_command_spec(action: ActionName) -> CommandSpec | None:
    return _client_instance.get_command_spec(action)


def list_actions_client() -> list[ActionName]:
    return _client_instance.list_actions()


def filter_by_domain(domain: DomainRef) -> dict[ActionName, CommandSpec]:
    return _client_instance.filter_by_domain(domain)
