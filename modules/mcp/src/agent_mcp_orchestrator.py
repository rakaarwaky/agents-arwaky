"""MCP agent orchestrator — single-execute aggregate over two subsystems.

Routes each ``McpRequest.op`` to the matching protocol method on the
injected list (discovery) or write (mutation) capability, then wraps
the result in a ``McpResponse``.
"""

from __future__ import annotations

from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.mcp.contract_mcp_protocol import (
    IMcpListProtocol,
    IMcpWriteProtocol,
)
from modules.shared.src.mcp.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpOp,
    McpRequest,
    McpResponse,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class McpOrchestrator(IMcpAggregate):
    """Single entry point over the MCP generator; dispatch happens here."""

    def __init__(
        self,
        list_cap: IMcpListProtocol,
        write_cap: IMcpWriteProtocol,
    ) -> None:
        """Inject the generator the orchestrator delegates to."""
        self._list = list_cap
        self._write = write_cap

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: McpRequest) -> McpResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = McpOp(str(request.op))
        output = request.output
        if op == "list":
            return McpResponse(self._list.list_servers())
        if op == "generate":
            return McpResponse(
                self._write.generate(output) if output is not None else ExitCode(1)
            )
        if op in {"show", "probe", "path"}:
            return McpResponse(self._list.show_server(request.server_id))
        if op == "alias":
            if request.alias is None or output is None:
                return McpResponse(ExitCode(1))
            return McpResponse(self._write.generate_alias(McpAlias(str(request.alias)), output))
        if op == "validate":
            return McpResponse(self._write.validate(output))
        return McpResponse(ExitCode(1))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "McpOrchestrator()"

__all__ = ["McpOrchestrator"]