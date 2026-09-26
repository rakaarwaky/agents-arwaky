"""Harness-domain aggregate contract (agent orchestrator ABC).

The single agent is the one door consumers (surface / root / CLI / MCP) knock
on. It resolves raw CLI tokens to canonical harness ids, routes each action
(connect / disconnect / provision_skills) to its capability, and returns a
single ``HarnessResponse``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_harness_vo import (
    HarnessRequest,
    HarnessResponse,
)


class IHarnessAggregate(ABC):
    """Aggregate over the harness domain: one entry point, one response."""

    @abstractmethod
    def execute(self, request: HarnessRequest) -> HarnessResponse:
        """Run the request the surface/CLI/root asked for; return the response."""
        ...


__all__ = ["HarnessRequest", "HarnessResponse", "IHarnessAggregate"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "HarnessRequest": HarnessRequest,
    "HarnessResponse": HarnessResponse,
    "IHarnessAggregate": IHarnessAggregate,
}
