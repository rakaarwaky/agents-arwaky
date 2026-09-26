"""Check-domain aggregate contract (agent orchestrator ABC).

Single entry point over the check feature: the surface, root, CLI and MCP
call ``execute`` with a request and get a response back. The agent behind
the aggregate routes each ``scope`` to the matching protocol method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_check_vo import CheckRequest, CheckResponse


class ICheckAggregate(ABC):
    """Single entry point over check verification; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: CheckRequest) -> CheckResponse:
        """Run the request the surface/root/CLI/MCP asked for; return the response."""
        ...


__all__ = ["CheckRequest", "CheckResponse", "ICheckAggregate"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "CheckRequest": CheckRequest,
    "CheckResponse": CheckResponse,
    "ICheckAggregate": ICheckAggregate,
}
