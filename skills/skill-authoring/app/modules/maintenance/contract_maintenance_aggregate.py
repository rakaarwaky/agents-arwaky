"""Maintenance-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the maintenance-side capabilities:
prune, purge.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.design.contract_skills_protocol import (
    ISkillsPruneProtocol,
    ISkillsPurgeProtocol,
)
from shared.src.design.taxonomy_skills_request import SkillsRequest
from shared.src.design.taxonomy_skills_response import SkillsResult

__all__ = [
    "ISkillsMaintenanceAggregate",
    "ISkillsPruneProtocol",
    "ISkillsPurgeProtocol",
]


class ISkillsMaintenanceAggregate(ABC):
    """Single entry point over maintenance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
