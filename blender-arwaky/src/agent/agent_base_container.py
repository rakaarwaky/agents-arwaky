"""
Agent Base Container - Core wiring for infrastructure and capabilities.
Part of the split to satisfy AES004 (file size).
"""

import logging

from contract import AgentBaseContainerAggregate
from taxonomy import SuccessFlag

from .agent_logic_coordinator import ContainerLogic

logger = logging.getLogger("BlenderMCPServer")


class AgentBaseContainer(ContainerLogic, AgentBaseContainerAggregate):
    """
    Base container handling infrastructure and capability managers.
    Satisfies the requirement for 13 agents = 13 Aggregates.
    """

    _success_ref: SuccessFlag = SuccessFlag(True)

    def __init__(self) -> None:
        super().__init__()
