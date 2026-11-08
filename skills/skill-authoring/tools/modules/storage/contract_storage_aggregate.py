"""Storage-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the storage-side capabilities:
archiver, backup, restore, rollback.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.design.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsBackupProtocol,
    ISkillsRestoreProtocol,
    ISkillsRollbackProtocol,
)
from shared.src.design.taxonomy_skills_request import SkillsRequest
from shared.src.design.taxonomy_skills_response import SkillsResult

__all__ = [
    "ISkillsStorageAggregate",
    "ISkillsArchiverProtocol",
    "ISkillsBackupProtocol",
    "ISkillsRestoreProtocol",
    "ISkillsRollbackProtocol",
]


class ISkillsStorageAggregate(ABC):
    """Single entry point over storage-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
