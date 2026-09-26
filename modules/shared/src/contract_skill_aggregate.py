"""Skill-domain aggregate contract (agent orchestrator ABC).

Single entry point over the skill feature: the surface, root, CLI and MCP
call ``execute`` with a request and get a response back. The agent behind
the aggregate routes each ``op`` to the matching protocol method on either
the provisioner or the registry.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_skill_vo import SkillRequest, SkillResponse


class ISkillAggregate(ABC):
    """Single entry point over skill management; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillRequest) -> SkillResponse:
        """Run the request the surface/root/CLI/MCP asked for; return the response."""
        ...


__all__ = ["ISkillAggregate", "SkillRequest", "SkillResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ISkillAggregate": ISkillAggregate,
    "SkillRequest": SkillRequest,
    "SkillResponse": SkillResponse,
}
