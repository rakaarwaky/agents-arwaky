"""MCP agent orchestrator — aggregates the MCP config generator."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from modules.shared.src.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpServer,
    McpServerId,
    McpServerInfo,
)


class _McpGenerator(Protocol):
    """Structural view of the internal generator methods the orchestrator drives."""

    def list_servers(self) -> list[McpServerInfo]: ...
    def show_server(self, server_id: McpServerId | None = None) -> ExitCode: ...
    def generate(self, output: Path) -> ExitCode: ...
    def generate_alias(self, alias: McpAlias, output: Path) -> ExitCode: ...
    def validate(self, output: Path | None = None) -> ExitCode: ...


# ─── Block 1: Class Definition & Constructor ──────────────
class McpOrchestrator(IMcpAggregate):
    """Pure delegation to the injected generator (zero I/O)."""

    def __init__(self, generator: _McpGenerator) -> None:
        self._generator = generator

    # ─── Block 2: Aggregate Method Implementation ──────────
    def list_servers(self) -> list[McpServerInfo]:
        return self._generator.list_servers()

    def show_server(self, server_id: McpServerId | None = None) -> ExitCode:
        return ExitCode(int(self._generator.show_server(server_id)))

    def generate(self, output: Path) -> ExitCode:
        return ExitCode(int(self._generator.generate(output)))

    def generate_alias(self, alias: McpAlias, output: Path) -> ExitCode:
        """Write an alias-qualified client config via the same generator."""
        return ExitCode(int(self._generator.generate_alias(alias, output)))

    def validate(self, output: Path | None = None) -> ExitCode:
        """Parse the generated config at *output* and report validity."""
        return ExitCode(int(self._generator.validate(output)))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "McpOrchestrator()"


__all__ = ["ExitCode", "McpAlias", "McpServer", "McpServerId", "McpServerInfo"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "McpAlias": McpAlias,
    "McpServer": McpServer,
    "McpServerId": McpServerId,
    "McpServerInfo": McpServerInfo,
}
