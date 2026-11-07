"""Governance-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the governance-side capabilities:
locker, piner, mover.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.skills_design.contract_skills_protocol import (
    ISkillsLockerProtocol,
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
)
from shared.src.skills_design.taxonomy_skills_request import SkillsRequest
from shared.src.skills_design.taxonomy_skills_response import SkillsResult

__all__ = [
    "ISkillsGovernanceAggregate",
    "ISkillsLockerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
]


class ISkillsGovernanceAggregate(ABC):
    """Single entry point over governance-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
