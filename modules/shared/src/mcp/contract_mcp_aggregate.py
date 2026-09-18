"""MCP-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IMcpAggregate(ABC):
    """Aggregate over MCP config listing, inspection and generation."""

    @abstractmethod
    def list_servers(self) -> list[dict[str, object]]:
        """List MCP-enabled tools (id, category, description)."""
        raise NotImplementedError

    @abstractmethod
    def show_server(self) -> int:
        """Print the generated MCP config path and contents; return exit code."""
        raise NotImplementedError

    @abstractmethod
    def generate_config(self, output: Path) -> int:
        """Regenerate the unified MCP config; return exit code."""
        raise NotImplementedError
