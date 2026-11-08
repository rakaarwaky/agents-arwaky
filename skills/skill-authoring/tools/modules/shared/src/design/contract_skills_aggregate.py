"""Skills-domain aggregate contract (AES contract layer, ABC trait).

The root CLI and surface call ``execute`` with a ``SkillsRequest`` and get a
``SkillsResult`` back. The orchestrator behind this interface routes each op
to the injected index/reader protocols.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.design.taxonomy_skills_request import SkillsRequest
from shared.src.design.taxonomy_skills_response import SkillsResult


class ISkillsAggregate(ABC):
    """Single entry point over skill-pack discovery; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...


__all__ = ["ISkillsAggregate"]
