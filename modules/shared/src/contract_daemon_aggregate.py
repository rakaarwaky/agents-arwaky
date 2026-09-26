"""Daemon-domain aggregate contract (agent orchestrator ABC).

Single entry point over the daemon feature: the surface, root, CLI and MCP
call ``execute`` with a request and get a response back. The agent behind the
aggregate routes each ``op`` to the matching protocol method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import DaemonRequest, DaemonResponse


class IDaemonAggregate(ABC):
    """Single entry point over daemon lifecycle and unit actions."""

    @abstractmethod
    def execute(self, request: DaemonRequest) -> DaemonResponse:
        """Run the request the surface/root/CLI/MCP asked for; return the response."""
        ...


__all__ = ["DaemonRequest", "DaemonResponse", "IDaemonAggregate"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonRequest": DaemonRequest,
    "DaemonResponse": DaemonResponse,
    "IDaemonAggregate": IDaemonAggregate,
}
