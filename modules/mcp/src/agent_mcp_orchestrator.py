"""MCP agent orchestrator — aggregates the MCP config generator."""
from __future__ import annotations
from modules.shared.src.taxonomy_mcp_vo import ExitCode, McpServer, McpServerInfo


from pathlib import Path

from modules.shared.src.contract_mcp_aggregate import IMcpAggregate


class McpOrchestrator(IMcpAggregate):
    """Pure delegation to the injected generator.

    # Block 1: Constructor
    # Block 2: Aggregate verb delegation
    # Block 3: Default output resolution
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, generator: IMcpAggregate) -> None:
        self._generator = generator

    # -- Block 2: Aggregate verb delegation ----------------------------------------
    def list_servers(self) -> list[McpServerInfo]:
        return self._generator.list_servers()

    def show_server(self) -> int:
        return int(self._generator.show_server())

    def generate_config(self, output: Path) -> int:
        return int(self._generator.generate(output))

    def generate(self, output: Path) -> int:
        return int(self._generator.generate(output))

__all__ = ['ExitCode', 'McpServer', 'McpServerInfo']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "McpServer": McpServer, "McpServerInfo": McpServerInfo}
