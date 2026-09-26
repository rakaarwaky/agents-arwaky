"""MCP agent orchestrator — single-execute aggregate over the config generator.

Routes each ``McpRequest.op`` to the matching rich protocol method on the
injected generator, then wraps the result in a ``McpResponse``.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.contract_mcp_protocol import IMcpProtocol
from modules.shared.src.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpOp,
    McpRequest,
    McpResponse,
    McpServerId,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class McpOrchestrator(IMcpAggregate):
    """Single entry point over the MCP generator; dispatch happens here."""

    def __init__(self, generator: IMcpProtocol) -> None:
        """Inject the generator the orchestrator delegates to."""
        self._generator = generator

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: McpRequest) -> McpResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = McpOp(str(request.op))
        output = request.output
        if op == "list":
            return McpResponse(self._generator.list_servers())
        if op == "generate":
            return McpResponse(
                self._generator.generate(output) if output is not None else ExitCode(1)
            )
        if op in {"show", "probe", "path"}:
            return McpResponse(self._generator.show_server(request.server_id))
        if op == "alias":
            if request.alias is None or output is None:
                return McpResponse(ExitCode(1))
            return McpResponse(self._generator.generate_alias(McpAlias(str(request.alias)), Path(output)))
        if op == "validate":
            return McpResponse(self._generator.validate(output))
        return McpResponse(ExitCode(1))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "McpOrchestrator()"


__all__ = ["McpOrchestrator", "McpRequest", "McpResponse", "McpServerId"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "McpOrchestrator": McpOrchestrator,
    "McpRequest": McpRequest,
    "McpResponse": McpResponse,
    "McpServerId": McpServerId,
}
