"""Check composition root — wires the 2 check runners (docs, skills) into the orchestrator."""
from __future__ import annotations

from modules.check.src.agent_check_orchestrator import CheckOrchestrator
from modules.check.src.capabilities_check_docs import DocsCheckRunner
from modules.check.src.capabilities_check_skills import SkillsCheckRunner
from modules.check.src.capabilities_doc_pack import DocPackRunner
from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.contract_check_protocol import ICheckRunner


class CheckContainer:
    """Construct the 2 check runners and the orchestrator."""

    def __init__(self) -> None:
        self._doc_pack_runner = DocPackRunner()
        runners: list[ICheckRunner] = [
            DocsCheckRunner(),
            SkillsCheckRunner(),
        ]
        self._orchestrator = CheckOrchestrator(runners)

    @property
    def aggregate(self) -> ICheckAggregate:
        return self._orchestrator


def create_check_feature() -> ICheckAggregate:
    """Fully-wired check feature aggregate."""
    return CheckContainer().aggregate
