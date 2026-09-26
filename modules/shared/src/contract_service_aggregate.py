"""Service-domain aggregate contract (agent orchestrator ABC).

Single entry point over the service feature: the surface, root, CLI and MCP
call ``execute`` with a request and get a response back. The agent behind the
aggregate routes each ``op`` to the matching protocol method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_service_vo import ServiceRequest, ServiceResponse


class IServiceAggregate(ABC):
    """Single entry point over service management; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: ServiceRequest) -> ServiceResponse:
        """Run the request the surface/root/CLI/MCP asked for; return the response."""
        ...


__all__ = ["IServiceAggregate", "ServiceRequest", "ServiceResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "IServiceAggregate": IServiceAggregate,
    "ServiceRequest": ServiceRequest,
    "ServiceResponse": ServiceResponse,
}
