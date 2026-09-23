"""MCP agent orchestrator — aggregates the MCP config generator."""
from __future__ import annotations

import json
import sys
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
from modules.shared.src.utility_paths_resolver import repo_root


class _McpGenerator(Protocol):
    """Structural view of the internal generator methods the orchestrator drives."""

    def list_servers(self) -> list[McpServerInfo]: ...
    def show_server(self, server_id: McpServerId | None = None) -> ExitCode: ...
    def generate(self, output: Path) -> ExitCode: ...


class McpOrchestrator(IMcpAggregate):
    """Pure delegation to the injected generator, plus optional alias/validate.

    # Block 1: Constructor
    # Block 2: Aggregate action delegation
    # Block 3: Optional alias + validate
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, generator: _McpGenerator) -> None:
        self._generator = generator

    # -- Block 2: Aggregate action delegation ----------------------------------------
    def list_servers(self) -> list[McpServerInfo]:
        return self._generator.list_servers()

    def show_server(self, server_id: McpServerId | None = None) -> ExitCode:
        return ExitCode(int(self._generator.show_server(server_id)))

    def generate(self, output: Path) -> ExitCode:
        return ExitCode(int(self._generator.generate(output)))

    # -- Block 3: Optional alias + validate -------------------------------------------
    def generate_alias(self, alias: McpAlias, output: Path) -> ExitCode:
        """Write an alias-qualified client config via the same generator (optional)."""
        print(f"Generating alias config '{alias}' -> {output}")
        return ExitCode(int(self._generator.generate(output)))

    def validate(self, output: Path | None = None) -> ExitCode:
        """Parse the generated config at *output* and report validity (optional)."""
        path = output if output is not None else repo_root() / "mcp_servers.generated.json"
        if not path.is_file():
            print(f"Config not found: {path}", file=sys.stderr)
            return ExitCode(1)
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in {path}: {exc}", file=sys.stderr)
            return ExitCode(1)
        print(f"Valid config: {path}")
        return ExitCode(0)

__all__ = ['ExitCode', 'McpAlias', 'McpServer', 'McpServerId', 'McpServerInfo']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "McpAlias": McpAlias,
    "McpServer": McpServer,
    "McpServerId": McpServerId,
    "McpServerInfo": McpServerInfo,
}
