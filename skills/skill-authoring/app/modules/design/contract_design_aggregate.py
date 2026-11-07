"""Design-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the design-side capabilities:
creator, adopter, linter, runner. The root CLI and surface call
``execute`` with a ``SkillsRequest`` and get a ``SkillsResult`` back.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.skills_design.contract_skills_protocol import (
    ISkillsAdopterProtocol,
    ISkillsCreatorProtocol,
    ISkillsLinterProtocol,
    ISkillsRunnerProtocol,
)
from shared.src.skills_design.taxonomy_skills_request import SkillsRequest
from shared.src.skills_design.taxonomy_skills_response import SkillsResult

__all__ = [
    "ISkillsDesignAggregate",
    "ISkillsAdopterProtocol",
    "ISkillsCreatorProtocol",
    "ISkillsLinterProtocol",
    "ISkillsRunnerProtocol",
]


class ISkillsDesignAggregate(ABC):
    """Single entry point over design-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
