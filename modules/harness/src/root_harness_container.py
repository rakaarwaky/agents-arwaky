"""Harness composition root — creates all 5 connectors and the orchestrator."""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.harness.src.capabilities_harness_antigravity import AntigravityConnector
from modules.harness.src.capabilities_harness_grok_build import GrokBuildConnector
from modules.harness.src.capabilities_harness_hermes import HermesConnector
from modules.harness.src.capabilities_harness_opencode import OpencodeConnector
from modules.harness.src.capabilities_harness_qwencode import QwencodeConnector
from modules.harness.contract.contract_harness_aggregate import IHarnessAggregate
from modules.harness.contract.contract_harness_protocol import IHarnessConnector


class HarnessContainer:
    """Construct the 5 harness connectors and the routing orchestrator."""

    def __init__(self) -> None:
        connectors: dict[str, IHarnessConnector] = {
            "antigravity": AntigravityConnector(),
            "hermes": HermesConnector(),
            "opencode": OpencodeConnector(),
            "qwencode": QwencodeConnector(),
            "grok-build": GrokBuildConnector(),
        }
        self._orchestrator = HarnessOrchestrator(connectors)

    @property
    def aggregate(self) -> IHarnessAggregate:
        return self._orchestrator


def create_harness_feature() -> IHarnessAggregate:
    """Fully-wired harness feature aggregate."""
    return HarnessContainer().aggregate
