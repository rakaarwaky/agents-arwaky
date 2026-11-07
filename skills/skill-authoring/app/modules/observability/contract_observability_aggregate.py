"""Observability-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the observability-side capabilities:
ledger, telemetry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.skills_design.contract_skills_protocol import (
    ISkillsLedgerProtocol,
    ISkillsTelemetryProtocol,
)
from shared.src.skills_design.taxonomy_skills_request import SkillsRequest
from shared.src.skills_design.taxonomy_skills_response import SkillsResult

__all__ = [
    "ISkillsObservabilityAggregate",
    "ISkillsLedgerProtocol",
    "ISkillsTelemetryProtocol",
]


class ISkillsObservabilityAggregate(ABC):
    """Single entry point over observability-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
