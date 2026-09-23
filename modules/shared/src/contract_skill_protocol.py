"""Skill-domain protocol contract (one feature, one capability ABC).

Provisioners, registries, and the registry adapter implement the single
``execute`` entry that covers every skill capability.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_skill_vo import ExitCode, SkillName, SkillOp


class ISkillProtocol(ABC):
    """Capability contract: one ``execute`` covering provision, audit, query, remove, sync."""

    @abstractmethod
    def execute(
        self,
        op: SkillOp,
        skill: SkillName | None = None,
        target: Path | None = None,
    ) -> ExitCode:
        """Run one skill *op* (``provision`` | ``audit`` | ``query`` | ``remove`` | ``sync``); return exit code.

        Args:
            op: Which capability to run.
            skill: Tool or skill name the op applies to; None targets the whole pack.
            target: Workspace directory the op provisions into or reads from.
        """
        ...


__all__ = [
    "ExitCode",
    "ISkillProtocol",
    "SkillName",
    "SkillOp",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "ISkillProtocol": ISkillProtocol,
    "SkillName": SkillName,
    "SkillOp": SkillOp,
}
