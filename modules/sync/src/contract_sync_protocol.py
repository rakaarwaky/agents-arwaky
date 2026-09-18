
from abc import ABC, abstractmethod


class ISyncRunner(ABC):
    """Capability contract for the one-shot ecosystem sync."""

    @abstractmethod
    def run(self, no_connect: bool, no_update: bool) -> int:
        """Run the 4-step sync (update, mcp generate, connect, check)."""
        raise NotImplementedError
