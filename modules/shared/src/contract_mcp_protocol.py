"""MCP-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_mcp_vo import (
    ExitCode,
    McpOp,
    McpServer,
    McpServerId,
)


class IMcpProtocol(ABC):
    """Capability contract: one ``execute`` covering generate, list and probe."""

    @abstractmethod
    def execute(
        self,
        op: McpOp,
        output: Path | None = None,
        server_id: McpServerId | None = None,
    ) -> ExitCode:
        """Run one MCP *op* (``generate`` | ``list`` | ``show``); return exit code.

        Args:
            op: Which capability to run.
            output: Target path for ``generate`` (defaults handled by the implementor).
            server_id: Server to probe for ``show``; ``None`` reports the whole config.
        """
        ...


__all__ = ['ExitCode', 'IMcpProtocol', 'McpOp', 'McpServer', 'McpServerId']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IMcpProtocol": IMcpProtocol,
    "McpOp": McpOp,
    "McpServer": McpServer,
    "McpServerId": McpServerId,
}
