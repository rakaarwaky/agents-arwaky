"""MCP-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_mcp_vo import ExitCode, McpServer


class IMcpConfigProtocol(ABC):
    """Capability contract for generating the unified MCP client config."""

    @abstractmethod
    def generate(self, output: Path) -> ExitCode:
        """Write the generated MCP config to *output*; return exit code."""
        ...

__all__ = ['ExitCode', 'IMcpConfigProtocol', 'McpServer']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IMcpConfigProtocol": IMcpConfigProtocol, "McpServer": McpServer}
