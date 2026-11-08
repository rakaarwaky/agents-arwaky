"""Trace-domain aggregate contract (AES contract layer, self-contained in ``app``).

Single entry point over the trace-side capabilities: scan sessions, mine
repeated phrases. The root CLI and surface call ``execute`` with a
``SkillsRequest`` and get a ``SkillsResult`` back.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.traces.contract_traces_protocol import ISkillsTracesProtocol
from shared.src.traces.taxonomy_traces_request import SkillsRequest
from shared.src.traces.taxonomy_traces_response import SkillsResult


class ISkillsTracesAggregate(ABC):
    """Single entry point over trace-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...


__all__ = ["ISkillsTracesAggregate", "ISkillsTracesProtocol"]
