"""MCP agent orchestrator — aggregates the MCP config generator."""
from __future__ import annotations

from pathlib import Path

from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator
from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate


class McpOrchestrator(IMcpAggregate):
    """Pure delegation to the injected generator.

    # Block 1: Constructor
    # Block 2: Aggregate verb delegation
    # Block 3: Default output resolution
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, generator: McpConfigGenerator) -> None:
        self._generator = generator

    # -- Block 2: Aggregate verb delegation ----------------------------------------
    def list_servers(self) -> list[dict[str, object]]:
        return self._generator.list_servers()

    def show_server(self) -> int:
        return self._generator.show_server()

    def generate_config(self, output: Path) -> int:
        return self._generator.generate(output)
