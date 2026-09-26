"""Config-domain aggregate contract — single ``execute`` entry point.

The root CLI and surface layer call ``execute`` with a ``ConfigRequest`` and
get a ``ConfigResult`` back. The orchestrator behind this interface routes each
``op`` to the matching protocol method on the injected capabilities.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import ConfigRequest, ConfigResult


class IConfigAggregate(ABC):
    """Single entry point over config management; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: ConfigRequest) -> ConfigResult:
        """Run the request the surface/root/CLI/MCP asked for; return the response."""
        ...


__all__ = [
    "IConfigAggregate",
    "ConfigRequest",
    "ConfigResult",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "IConfigAggregate": IConfigAggregate,
    "ConfigRequest": ConfigRequest,
    "ConfigResult": ConfigResult,
}
