"""Check composition root — wires the 5 check runners into the orchestrator."""
from __future__ import annotations

from modules.check.src.agent_check_orchestrator import CheckOrchestrator
from modules.check.src.capabilities_check_docs import DocsCheckRunner
from modules.check.src.capabilities_check_json import JsonCheckRunner
from modules.check.src.capabilities_check_python import PythonCheckRunner
from modules.check.src.capabilities_check_shell import ShellCheckRunner
from modules.check.src.capabilities_check_skills import SkillsCheckRunner
from modules.check.contract.contract_check_aggregate import ICheckAggregate
from modules.check.contract.contract_check_protocol import ICheckRunner


class CheckContainer:
    """Construct the 5 check runners and the orchestrator."""

    def __init__(self) -> None:
        runners: list[ICheckRunner] = [
            JsonCheckRunner(),
            PythonCheckRunner(),
            DocsCheckRunner(),
            SkillsCheckRunner(),
            ShellCheckRunner(),
        ]
        self._orchestrator = CheckOrchestrator(runners)

    @property
    def aggregate(self) -> ICheckAggregate:
        return self._orchestrator


def create_check_feature() -> ICheckAggregate:
    """Fully-wired check feature aggregate."""
    return CheckContainer().aggregate
