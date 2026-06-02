"""
Contract: Port interface for command catalog queries.

Defines the contract for querying the domain command catalog
(action list, command specs, domain-based filtering).
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import ActionName, DomainRef
from taxonomy.blender_command_vo import CommandSpec


class CommandCatalogPort(ABC):
    """Port interface for querying the command catalog."""

    @abstractmethod
    def get_command_spec(self, action: ActionName) -> CommandSpec | None:
        """Retrieve command spec for a named action."""
        pass

    @abstractmethod
    def list_actions(self) -> list[ActionName]:
        """Return all available action names."""
        pass

    @abstractmethod
    def filter_by_domain(self, domain: DomainRef) -> dict[ActionName, CommandSpec]:
        """Return command specs filtered by domain."""
        pass
