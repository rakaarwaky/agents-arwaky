"""MCP-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IMcpConfigGenerator(ABC):
    """Capability contract for generating the unified MCP client config."""

    @abstractmethod
    def generate(self, output: Path) -> int:
        """Write the generated MCP config to *output*; return exit code."""
        raise NotImplementedError
