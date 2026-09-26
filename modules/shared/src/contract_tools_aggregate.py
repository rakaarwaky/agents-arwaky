"""Tool-domain aggregate contract (AES102 `_aggregate`).

The single entry point over the tools feature. Consumers pass a
`ToolRequest`; the agent behind the aggregate dispatches to the rich
protocol classes in `contract_tools_protocol.py`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_tools_vo import ToolRequest, ToolResponse


class IToolsAggregate(ABC):
    """Single entry point over the tools feature."""

    @abstractmethod
    def execute(self, request: ToolRequest) -> ToolResponse:
        """Run the requested operation; return its response."""
        ...


__all__ = ["IToolsAggregate", "ToolRequest", "ToolResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "IToolsAggregate": IToolsAggregate,
    "ToolRequest": ToolRequest,
    "ToolResponse": ToolResponse,
}
